import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.utils.app_logger import AppLogger
from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
    MessageThreadDTO,
    MessageType,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.repository.extension_sessions.repository import (
    ExtensionSessionsRepository,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
    ParsedLLMCallResponse,
    PromptCacheConfig,
    StreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.constants.tool_fallback import EXCEPTION_RAISED_FALLBACK
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryData
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.chat_history_handler import (
    ChatHistoryHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclasses.main import (
    PreviousChatPayload,
)
from app.main.blueprints.one_dev.services.query_solver.agents.base_query_solver_agent import QuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.agents.custom_query_solver_agent import (
    CustomQuerySolverAgent,
)
from app.main.blueprints.one_dev.services.query_solver.agents.default_query_solver_agent import (
    DefaultQuerySolverAgentInstance,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    DetailedDirectoryItem,
    DetailedFocusItem,
    QuerySolverInput,
    ResponseMetadataBlock,
    ResponseMetadataContent,
    ToolUseResponseInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    StreamingContentBlockType,
)
from app.main.blueprints.one_dev.services.repository.query_solver_agents.repository import QuerySolverAgentsRepository
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)
from app.main.blueprints.one_dev.utils.cancellation_checker import (
    CancellationChecker,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.version import compare_version

from .agent_selector.agent_selector import QuerySolverAgentSelector
from .prompts.factory import PromptFeatureFactory


class QuerySolver:
    async def _generate_session_summary(
        self,
        session_id: int,
        query: str,
        focus_items: List[DetailedFocusItem],
        directory_items: Optional[List[DetailedDirectoryItem]],
        llm_handler: LLMHandler[PromptFeatures],
        user_team_id: int,
        session_type: str,
    ) -> None:
        current_session = await ExtensionSessionsRepository.find_or_create(session_id, user_team_id, session_type)
        if current_session and current_session.summary:
            return

        # if no summary, first generate a summary by directly putting first 100 characters of the query.
        # this will be used as a placeholder until the LLM generates a more detailed summary.
        brief_query_preview = query[:100]
        await ExtensionSessionsRepository.update_session_summary(
            session_id=session_id, summary=f"{brief_query_preview}..."
        )

        # then generate a more detailed summary using LLM
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.SESSION_SUMMARY_GENERATOR,
            llm_model=LLModels.GEMINI_2_POINT_5_FLASH,
            prompt_vars={"query": query, "focus_items": focus_items, "directory_items": directory_items},
            previous_responses=[],
            tools=[],
            stream=False,
            session_id=session_id,
            call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("Expected NonStreamingParsedLLMCallResponse")

        generated_summary = llm_response.parsed_content[0].get("summary")
        await ExtensionSessionsRepository.update_session_summary(session_id=session_id, summary=generated_summary)

    async def get_previous_message_thread_ids(self, session_id: int, previous_query_ids: List[int]) -> List[int]:
        all_previous_responses = await MessageThreadsRepository.get_message_threads_for_session(
            session_id, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
        )
        all_previous_responses.sort(key=lambda x: x.id, reverse=False)

        if not all_previous_responses:
            return []

        if not previous_query_ids:
            return [response.id for response in all_previous_responses]

        return [
            response.id
            for response in all_previous_responses
            if response.query_id in previous_query_ids or response.id in previous_query_ids
        ]

    async def get_relevant_chat_history_ids(self, session_id: int, query: str, llm_model: str) -> List[int]:
        """
        Fetch relevant chat history IDs for the given query.
        """
        try:
            chat_handler = ChatHistoryHandler(
                PreviousChatPayload(query=query, session_id=session_id), llm_model=llm_model
            )
            response = await chat_handler.get_relevant_previous_chats()

            if response and "chats" in response:
                history_ids = [chat["id"] for chat in response["chats"]]
                return history_ids

            return []
        except Exception:  # noqa : BLE001
            return []

    async def _update_query_summary(self, query_id: int, summary: str, session_id: int) -> None:
        existing_summary = await QuerySummarysRepository.get_query_summary(session_id=session_id, query_id=query_id)
        if existing_summary:
            new_updated_summary = existing_summary.summary + "\n" + summary
            await QuerySummarysRepository.update_query_summary(
                session_id=session_id, query_id=query_id, summary=new_updated_summary
            )
        else:
            await QuerySummarysRepository.create_query_summary(
                QuerySummaryData(
                    session_id=session_id,
                    query_id=query_id,
                    summary=summary,
                )
            )

    async def get_final_stream_iterator(
        self, llm_response: ParsedLLMCallResponse, session_id: int
    ) -> AsyncIterator[BaseModel]:
        query_summary: Optional[str] = None

        async def _streaming_content_block_generator() -> AsyncIterator[BaseModel]:
            nonlocal llm_response
            nonlocal query_summary
            if not isinstance(llm_response, StreamingParsedLLMCallResponse):
                raise ValueError("Expected StreamingParsedLLMCallResponse")

            yield ResponseMetadataBlock(
                content=ResponseMetadataContent(query_id=llm_response.query_id, session_id=session_id),
                type="RESPONSE_METADATA",
            )

            async for data_block in llm_response.parsed_content:
                # Check if the current task is cancelled
                current_task = asyncio.current_task()
                if current_task and current_task.cancelled():
                    raise asyncio.CancelledError("Task cancelled in QuerySolver")

                if data_block.type in [
                    StreamingContentBlockType.SUMMARY_BLOCK_START,
                    StreamingContentBlockType.SUMMARY_BLOCK_DELTA,
                    StreamingContentBlockType.SUMMARY_BLOCK_END,
                ]:
                    if data_block.type == StreamingContentBlockType.SUMMARY_BLOCK_DELTA:
                        query_summary = (query_summary or "") + data_block.content.summary_delta

                    elif data_block.type == StreamingContentBlockType.SUMMARY_BLOCK_END and query_summary:
                        asyncio.create_task(
                            self._update_query_summary(llm_response.query_id, query_summary, session_id)
                        )

                else:
                    yield data_block

            # wait till the data has been stored in order to ensure that no race around occurs in submitting tool response
            await llm_response.llm_response_storage_task

        return _streaming_content_block_generator()

    async def _generate_dynamic_query_solver_agents(self) -> List[CustomQuerySolverAgent]:
        # get all the intents from the database
        all_agents = await QuerySolverAgentsRepository.get_query_solver_agents()
        if not all_agents:
            return []

        # create a list of agent classes based on the data from the database
        agent_classes: List[CustomQuerySolverAgent] = []
        for agent_data in all_agents:
            agent_class = CustomQuerySolverAgent(
                agent_name=agent_data.name,
                agent_description=agent_data.description,
                allowed_tools=agent_data.allowed_first_party_tools,
                prompt_intent=agent_data.prompt_intent,
            )
            agent_classes.append(agent_class)

        return agent_classes

    async def get_last_query_message_for_session(self, session_id: int) -> Optional[MessageThreadDTO]:
        """
        Get the last query message for the session.
        """
        try:
            messages = await MessageThreadsRepository.get_message_threads_for_session(
                session_id, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
            )
            last_query_message = None
            for message in messages:
                if message.message_type == MessageType.QUERY and message.prompt_type in [
                    "CODE_QUERY_SOLVER",
                    "CUSTOM_CODE_QUERY_SOLVER",
                ]:
                    last_query_message = message
            return last_query_message
        except Exception as ex:  # noqa: BLE001
            AppLogger.log_error(f"Error occurred while fetching last query message for session {session_id}: {ex}")
            return None

    async def _get_agent_instance_by_name(
        self, agent_name: str, all_agents: List[QuerySolverAgent]
    ) -> QuerySolverAgent:
        """
        Get the agent instance by its name.
        """
        for agent in all_agents:
            if agent.agent_name == agent_name:
                return agent
        return DefaultQuerySolverAgentInstance

    async def solve_query(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        save_to_redis: bool = False,
        task_checker: Optional[CancellationChecker] = None,
    ) -> AsyncIterator[BaseModel]:
        llm_handler = LLMHandler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )
        parallel_tool_use_enabled = compare_version(client_data.client_version, "8.4.0", ">=")

        # TODO: remove this after 9.0.0. force upgrade
        if payload.query is None and payload.batch_tool_responses is None and payload.tool_use_response is not None:
            payload.batch_tool_responses = [payload.tool_use_response]

        if payload.query:
            asyncio.create_task(
                self._generate_session_summary(
                    session_id=payload.session_id,
                    query=payload.query,
                    focus_items=payload.focus_items,
                    directory_items=payload.directory_items,
                    llm_handler=llm_handler,
                    user_team_id=payload.user_team_id,
                    session_type=payload.session_type,
                )
            )

            relevant_history_ids = await self.get_relevant_chat_history_ids(
                session_id=payload.session_id, query=payload.query, llm_model=payload.llm_model.value
            )
            previous_responses = await self.get_previous_message_thread_ids(payload.session_id, relevant_history_ids)
            last_query_message = await self.get_last_query_message_for_session(payload.session_id)
            all_custom_agents = await self._generate_dynamic_query_solver_agents()
            agent_selector = QuerySolverAgentSelector(
                user_query=payload.query,
                focus_items=payload.focus_items,
                directory_items=payload.directory_items if payload.directory_items else [],
                last_agent=last_query_message.metadata.get("agent_name")
                if last_query_message and last_query_message.metadata
                else None,
                all_agents=[*all_custom_agents, DefaultQuerySolverAgentInstance],
                llm_handler=llm_handler,
                session_id=payload.session_id,
            )

            agent_instance = (
                (await agent_selector.select_agent() or DefaultQuerySolverAgentInstance)
                if all_custom_agents
                else DefaultQuerySolverAgentInstance
            )
            if not agent_instance:
                raise ValueError("No suitable agent found for the query.")

            prompt_vars_to_use: Dict[str, Any] = {
                "query": payload.query,
                "focus_items": payload.focus_items,
                "directory_items": payload.directory_items,
                "deputy_dev_rules": payload.deputy_dev_rules,
                "write_mode": payload.write_mode,
                "urls": [url.model_dump() for url in payload.urls],
                "os_name": payload.os_name,
                "shell": payload.shell,
                "vscode_env": payload.vscode_env,
                "repositories": payload.repositories,
                "parallel_tool_use_enabled": parallel_tool_use_enabled,  # remove after 9.0.0. force upgrade
            }

            model_to_use = LLModels(payload.llm_model.value)
            llm_inputs = agent_instance.get_llm_inputs(
                payload=payload, _client_data=client_data, llm_model=model_to_use, previous_messages=previous_responses
            )

            prompt_vars_to_use = {**prompt_vars_to_use, **llm_inputs.extra_prompt_vars}

            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures(llm_inputs.prompt.prompt_type),
                llm_model=model_to_use,
                prompt_vars=prompt_vars_to_use,
                attachments=payload.attachments,
                previous_responses=llm_inputs.previous_messages,
                tools=llm_inputs.tools,
                stream=True,
                session_id=payload.session_id,
                save_to_redis=save_to_redis,
                checker=task_checker,
                parallel_tool_calls=parallel_tool_use_enabled,
                prompt_handler_instance=llm_inputs.prompt(params=prompt_vars_to_use),
                metadata={
                    "agent_name": agent_instance.agent_name,
                },
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        elif payload.batch_tool_responses:
            prompt_vars: Dict[str, Any] = {
                "os_name": payload.os_name,
                "shell": payload.shell,
                "vscode_env": payload.vscode_env,
                "write_mode": payload.write_mode,
                "deputy_dev_rules": payload.deputy_dev_rules,
                "parallel_tool_use_enabled": parallel_tool_use_enabled,  # remove after 9.0.0. force upgrade
            }

            tool_responses = []
            for resp in payload.batch_tool_responses:
                if not payload.tool_use_failed:
                    response_data = self._format_tool_response(resp)
                else:
                    if resp.tool_name not in {"replace_in_file", "write_to_file"}:
                        response_data = {
                            "error_message": EXCEPTION_RAISED_FALLBACK.format(
                                tool_name=resp.tool_name,
                                error_type=resp.response.get("error_type", "Unknown") if resp.response else "Unknown",
                                error_message=resp.response.get(
                                    "error_message", "An error occurred while using the tool."
                                )
                                if resp.response
                                else "An error occurred while using the tool.",
                            )
                        }
                    else:
                        response_data = resp.response

                tool_responses.append(
                    ToolUseResponseData(
                        content=ToolUseResponseContent(
                            tool_name=resp.tool_name,
                            tool_use_id=resp.tool_use_id,
                            response=response_data,
                        )
                    )
                )

            last_query_message = await self.get_last_query_message_for_session(payload.session_id)
            agent_name = (
                last_query_message.metadata.get("agent_name")
                if last_query_message and last_query_message.metadata
                else None
            )
            agent_instance: QuerySolverAgent = await self._get_agent_instance_by_name(
                agent_name=agent_name or DefaultQuerySolverAgentInstance.agent_name,
                all_agents=[*await self._generate_dynamic_query_solver_agents(), DefaultQuerySolverAgentInstance],
            )
            llm_inputs = agent_instance.get_llm_inputs(
                payload=payload,
                _client_data=client_data,
                llm_model=LLModels(payload.llm_model.value if payload.llm_model else LLModels.CLAUDE_3_POINT_5_SONNET),
                previous_messages=None,
            )

            llm_response = await llm_handler.submit_batch_tool_use_response(
                session_id=payload.session_id,
                tool_use_responses=tool_responses,
                tools=llm_inputs.tools,
                stream=True,
                prompt_vars=prompt_vars,
                checker=task_checker,
                parallel_tool_calls=parallel_tool_use_enabled,
            )

            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        else:
            raise ValueError("Invalid input")

    def _format_tool_response(self, tool_use_response: ToolUseResponseInput) -> Dict[str, Any]:
        """Handle and structure tool responses based on tool type."""
        tool_response = tool_use_response.response

        if tool_use_response.tool_name == "focused_snippets_searcher":
            return {
                "chunks": [
                    ChunkInfo(**chunk).get_xml()
                    for search_response in tool_response["batch_chunks_search"]["response"]
                    for chunk in search_response["chunks"]
                ],
            }

        if tool_use_response.tool_name == "iterative_file_reader":
            return {
                "file_content_with_line_numbers": ChunkInfo(**tool_response["data"]["chunk"]).get_xml(),
                "eof_reached": tool_response["data"]["eof_reached"],
            }

        if tool_use_response.tool_name == "grep_search":
            return {
                "matched_contents": "".join(
                    [
                        f"<match_obj>{ChunkInfo(**matched_block['chunk_info']).get_xml()}<match_line>{matched_block['matched_line']}</match_line></match_obj>"
                        for matched_block in tool_response["data"]
                    ]
                ),
            }

        return tool_response if tool_response else {}
