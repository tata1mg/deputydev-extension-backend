import asyncio
from typing import AsyncIterator, List, Optional

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
    ParsedLLMCallResponse,
    StreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryData
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
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
from app.main.blueprints.one_dev.services.query_solver.tools.related_code_searcher import (
    RELATED_CODE_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.focused_snippets_searcher import (
    FOCUSED_SNIPPETS_SEARCHER,
)
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)

from .prompts.factory import PromptFeatureFactory
from deputydev_core.services.chunking.chunk_info import ChunkInfo


class QuerySolver:
    async def _generate_session_summary(self, session_id: int, query: str, llm_handler: LLMHandler[PromptFeatures]):
        current_session = await MessageSessionsRepository.get_by_id(session_id)
        if current_session and current_session.summary:
            return
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.SESSION_SUMMARY_GENERATOR,
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            prompt_vars={"query": query},
            previous_responses=[],
            tools=[],
            stream=False,
            session_id=session_id,
            call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("Expected NonStreamingParsedLLMCallResponse")

        generated_summary = llm_response.parsed_content[0].get("summary")
        await MessageSessionsRepository.update_session_summary(session_id=session_id, summary=generated_summary)

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

    async def solve_query(self, payload: QuerySolverInput) -> AsyncIterator[BaseModel]:

        tools_to_use = [RELATED_CODE_SEARCHER, ASK_USER_INPUT, FOCUSED_SNIPPETS_SEARCHER]

        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)

        if payload.query:
            asyncio.create_task(
                self._generate_session_summary(
                    session_id=payload.session_id, query=payload.query, llm_handler=llm_handler
                )
            )
            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures.CODE_QUERY_SOLVER,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                prompt_vars={"query": payload.query, "relevant_chunks": payload.relevant_chunks},
                previous_responses=await self.get_previous_message_thread_ids(
                    payload.session_id, payload.previous_query_ids
                ),
                tools=tools_to_use,
                stream=True,
                session_id=payload.session_id,
            )
            return await self.get_final_stream_iterator(llm_response, session_id=payload.session_id)

        elif payload.tool_use_response:
            print("Tool use response")
            print(payload.tool_use_response.response)

            tool_response = payload.tool_use_response.response
            if payload.tool_use_response.tool_name == "focused_snippets_searcher":
                tool_response = {
                    "chunks": [
                        ChunkInfo(**chunk).get_xml()
                        for search_response in tool_response["batch_chunks_search"]["response"]
                        for chunk in search_response["chunks"]
                    ],
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
