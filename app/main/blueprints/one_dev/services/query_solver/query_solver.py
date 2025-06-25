import asyncio
from typing import AsyncIterator, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.utils.config_manager import ConfigManager
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
    ConversationTool,
    NonStreamingParsedLLMCallResponse,
    ParsedLLMCallResponse,
    PromptCacheConfig,
    StreamingParsedLLMCallResponse
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.constants.tool_fallback import EXCEPTION_RAISED_FALLBACK
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryData
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClientTool,
    DetailedDirectoryItem,
    DetailedFocusItem,
    MCPToolMetadata,
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
from app.main.blueprints.one_dev.services.query_solver.tools.ask_user_input import (
    ASK_USER_INPUT,
)
from app.main.blueprints.one_dev.services.query_solver.tools.create_new_workspace import (
    CREATE_NEW_WORKSPACE,
)
from app.main.blueprints.one_dev.services.query_solver.tools.execute_command import (
    EXECUTE_COMMAND,
)
from app.main.blueprints.one_dev.services.query_solver.tools.file_editor import REPLACE_IN_FILE
from app.main.blueprints.one_dev.services.query_solver.tools.file_path_searcher import (
    FILE_PATH_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.focused_snippets_searcher import (
    FOCUSED_SNIPPETS_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.grep_search import (
    GREP_SEARCH,
)
from app.main.blueprints.one_dev.services.query_solver.tools.iterative_file_reader import (
    ITERATIVE_FILE_READER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.public_url_content_reader import (
    PUBLIC_URL_CONTENT_READER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.related_code_searcher import (
    RELATED_CODE_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.web_search import (
    WEB_SEARCH,
)
from app.main.blueprints.one_dev.services.query_solver.tools.write_to_file import WRITE_TO_FILE
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)
from app.main.blueprints.one_dev.utils.cancellation_checker import (
    CancellationChecker,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData

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
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
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

        async def _streaming_content_block_generator():
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
                if asyncio.current_task() and asyncio.current_task().cancelled():
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

    def generate_conversation_tool_from_client_tool(self, client_tool: ClientTool) -> ConversationTool:
        # check if tool is MCP type tool
        if isinstance(client_tool.tool_metadata, MCPToolMetadata):
            description_extra = f"This tool is provided by a third party MCP server - {client_tool.tool_metadata.server_id}. Please ensure that any data passed to this tool is exactly what is required to be sent to this tool to function properly. Do not supply any sensitive data to this tool which can be misused by the MCP server. In case of ambiguity, ask the user for clarification."
            return ConversationTool(
                name=client_tool.name,
                description=description_extra + "\n" + client_tool.description,
                input_schema=client_tool.input_schema,
            )
        raise ValueError(
            f"Unsupported tool metadata type: {type(client_tool.tool_metadata)} for tool {client_tool.name}"
        )

    def _get_all_tools(self, payload: QuerySolverInput, _client_data: ClientData) -> List[ConversationTool]:
        tools_to_use = [
            ASK_USER_INPUT,
            FOCUSED_SNIPPETS_SEARCHER,
            FILE_PATH_SEARCHER,
            ITERATIVE_FILE_READER,
            GREP_SEARCH,
            EXECUTE_COMMAND,
            CREATE_NEW_WORKSPACE,
            PUBLIC_URL_CONTENT_READER,
        ]

        if ConfigManager.configs["IS_RELATED_CODE_SEARCHER_ENABLED"] and payload.is_embedding_done:
            tools_to_use.append(RELATED_CODE_SEARCHER)
        if payload.search_web:
            tools_to_use.append(WEB_SEARCH)
        if payload.write_mode:
            tools_to_use.append(REPLACE_IN_FILE)
            tools_to_use.append(WRITE_TO_FILE)

        for client_tool in payload.client_tools:
            tools_to_use.append(self.generate_conversation_tool_from_client_tool(client_tool))

        return tools_to_use

    async def solve_query(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        save_to_redis: bool = False,
        task_checker: CancellationChecker = None,
    ) -> AsyncIterator[BaseModel]:
        tools_to_use = self._get_all_tools(payload=payload, _client_data=client_data)
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

            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures.CODE_QUERY_SOLVER,
                llm_model=LLModels(payload.llm_model.value),
                prompt_vars={
                    "query": payload.query,
                    "focus_items": payload.focus_items,
                    "directory_items": payload.directory_items,
                    "deputy_dev_rules": payload.deputy_dev_rules,
                    "write_mode": payload.write_mode,
                    "urls": [url.model_dump() for url in payload.urls],
                    "os_name": payload.os_name,
                    "shell": payload.shell,
                    "vscode_env": payload.vscode_env,
                },
                attachments=payload.attachments,
                previous_responses=await self.get_previous_message_thread_ids(
                    payload.session_id, payload.previous_query_ids
                ),
                tools=tools_to_use,
                stream=True,
                session_id=payload.session_id,
                save_to_redis=save_to_redis,
                checker=task_checker,
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        elif payload.tool_use_response:
            prompt_vars = {
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
                    tool_response = {
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
                tools=tools_to_use,
                stream=True,
                prompt_vars=prompt_vars,
                checker=task_checker,
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        else:
            raise ValueError("Invalid input")
