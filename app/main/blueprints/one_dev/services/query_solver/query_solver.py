import asyncio
from typing import AsyncIterator, List, Optional

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
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryData
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
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
from app.main.blueprints.one_dev.services.query_solver.tools.ask_user_input import (
    ASK_USER_INPUT,
)
from app.main.blueprints.one_dev.services.query_solver.tools.file_path_searcher import (
    FILE_PATH_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.focused_snippets_searcher import (
    FOCUSED_SNIPPETS_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.grep_search import (
    GREP_SEARCH,
)
from app.main.blueprints.one_dev.services.query_solver.tools.public_url_content_reader import (
    PUBLIC_URL_CONTENT_READER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.iterative_file_reader import (
    ITERATIVE_FILE_READER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.related_code_searcher import (
    RELATED_CODE_SEARCHER,
)
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.version import compare_version

from .prompts.factory import PromptFeatureFactory
from deputydev_core.utils.config_manager import ConfigManager

MIN_SUPPORTED_CLIENT_VERSION_FOR_ITERATIVE_FILE_READER = "2.0.0"
MIN_SUPPORTED_CLIENT_VERSION_FOR_GREP_SEARCH = "2.0.0"
MIN_SUPPORTED_CLIENT_VERSION_FOR_PUBLIC_URL_CONTENT_READER = "2.1.1"


class QuerySolver:
    async def _generate_session_summary(
        self,
        session_id: int,
        query: str,
        focus_items: List[DetailedFocusItem],
        llm_handler: LLMHandler[PromptFeatures],
        user_team_id: int,
        session_type: str,
    ):
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
            prompt_vars={"query": query, "focus_items": focus_items},
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

        return _streaming_content_block_generator()

    async def solve_query(self, payload: QuerySolverInput, client_data: ClientData) -> AsyncIterator[BaseModel]:

        tools_to_use = [
            ASK_USER_INPUT,
            FOCUSED_SNIPPETS_SEARCHER,
            FILE_PATH_SEARCHER,
        ]
        if ConfigManager.configs["IS_RELATED_CODE_SEARCHER_ENABLED"]:
            tools_to_use.append(RELATED_CODE_SEARCHER)

        if compare_version(client_data.client_version, MIN_SUPPORTED_CLIENT_VERSION_FOR_ITERATIVE_FILE_READER, ">="):
            tools_to_use.append(ITERATIVE_FILE_READER)

        if compare_version(client_data.client_version, MIN_SUPPORTED_CLIENT_VERSION_FOR_GREP_SEARCH, ">="):
            tools_to_use.append(GREP_SEARCH)

        if compare_version(
            client_data.client_version, MIN_SUPPORTED_CLIENT_VERSION_FOR_PUBLIC_URL_CONTENT_READER, ">="
        ):
            tools_to_use.append(PUBLIC_URL_CONTENT_READER)

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
                    llm_handler=llm_handler,
                    user_team_id=payload.user_team_id,
                    session_type=payload.session_type,
                )
            )

            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures.CODE_QUERY_SOLVER,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                prompt_vars={
                    "query": payload.query,
                    "focus_items": payload.focus_items,
                    "deputy_dev_rules": payload.deputy_dev_rules,
                    "write_mode": payload.write_mode,
                },
                previous_responses=await self.get_previous_message_thread_ids(
                    payload.session_id, payload.previous_query_ids
                ),
                tools=tools_to_use,
                stream=True,
                session_id=payload.session_id,
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        elif payload.tool_use_response:
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
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        else:
            raise ValueError("Invalid input")
