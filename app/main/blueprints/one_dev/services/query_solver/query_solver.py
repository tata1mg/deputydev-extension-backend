import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
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
from app.main.blueprints.one_dev.services.query_solver.agents.backend_app_creator_query_solver_agent import (
    BackendAppCreatorQuerySolverAgent,
)
from app.main.blueprints.one_dev.services.query_solver.agents.default_query_solver_agent import DefaultQuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    DetailedDirectoryItem,
    DetailedFocusItem,
    QuerySolverInput,
    ResponseMetadataBlock,
    ResponseMetadataContent,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    StreamingContentBlockType,
)
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)
from app.main.blueprints.one_dev.utils.cancellation_checker import (
    CancellationChecker,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData

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

            previous_responses = await self.get_previous_message_thread_ids(
                payload.session_id, payload.previous_query_ids
            )
            agent_selector = QuerySolverAgentSelector(
                user_query=payload.query,
                focus_items=payload.focus_items,
                directory_items=payload.directory_items if payload.directory_items else [],
                all_agents=[BackendAppCreatorQuerySolverAgent, DefaultQuerySolverAgent],
                llm_handler=llm_handler,
                session_id=payload.session_id,
            )

            selected_agent = await agent_selector.select_agent()
            if not selected_agent:
                raise ValueError("No suitable agent found for the query.")

            # Create an instance of the selected agent
            agent_instance = selected_agent(previous_messages=previous_responses)

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
            }

            model_to_use = LLModels(payload.llm_model.value)
            llm_inputs = agent_instance.get_llm_inputs(
                payload=payload, _client_data=client_data, llm_model=model_to_use
            )

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
                prompt_handler_instance=llm_inputs.prompt(params=prompt_vars_to_use),
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        elif payload.tool_use_response:
            prompt_vars: Dict[str, Any] = {
                "os_name": payload.os_name,
                "shell": payload.shell,
                "vscode_env": payload.vscode_env,
                "write_mode": payload.write_mode,
                "deputy_dev_rules": payload.deputy_dev_rules,
            }
            tool_response = payload.tool_use_response.response
            if not payload.tool_use_failed:
                if payload.tool_use_response.tool_name == "focused_snippets_searcher":
                    tool_response = {
                        "chunks": [
                            ChunkInfo(**chunk).get_xml()
                            for search_response in tool_response["batch_chunks_search"]["response"]
                            for chunk in search_response["chunks"]
                        ],
                    }

                if payload.tool_use_response.tool_name == "iterative_file_reader":
                    tool_response: Dict[str, Any] = {
                        "file_content_with_line_numbers": ChunkInfo(**tool_response["data"]["chunk"]).get_xml(),
                        "eof_reached": tool_response["data"]["eof_reached"],
                    }

                if payload.tool_use_response.tool_name == "grep_search":
                    tool_response = {
                        "matched_contents": "".join(
                            [
                                f"<match_obj>{ChunkInfo(**matched_block['chunk_info']).get_xml()}<match_line>{matched_block['matched_line']}</match_line></match_obj>"
                                for matched_block in tool_response["data"]
                            ]
                        ),
                    }

            if payload.tool_use_failed:
                if payload.tool_use_response.tool_name not in {"replace_in_file", "write_to_file"}:
                    error_response = {
                        "error_message": EXCEPTION_RAISED_FALLBACK.format(
                            tool_name=payload.tool_use_response.tool_name,
                            error_type=tool_response.get("error_type", "Unknown"),
                            error_message=tool_response.get("error_message", "An error occurred while using the tool."),
                        )
                    }
                    tool_response = error_response

            llm_response = await llm_handler.submit_tool_use_response(
                session_id=payload.session_id,
                tool_use_response=ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name=payload.tool_use_response.tool_name,
                        tool_use_id=payload.tool_use_response.tool_use_id,
                        response=tool_response,
                    )
                ),
                tools=DefaultQuerySolverAgent().get_all_tools(payload=payload, _client_data=client_data),
                stream=True,
                prompt_vars=prompt_vars,
                checker=task_checker,
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        else:
            raise ValueError("Invalid input")
