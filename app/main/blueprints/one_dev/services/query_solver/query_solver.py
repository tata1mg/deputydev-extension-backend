import asyncio
from typing import List

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.repository.message_threads.repository import MessageThreadsRepository
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    QuerySolverInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.tools.ask_user_input import (
    ASK_USER_INPUT,
)
from app.main.blueprints.one_dev.services.query_solver.tools.code_searcher import (
    CODE_SEARCHER,
)

from .prompts.factory import PromptFeatureFactory


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

    async def get_previous_messages(self, session_id: int) -> List[int]:
        all_previous_responses = await MessageThreadsRepository.get_message_threads_for_session(
            session_id, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
        )

        return [response.id for response in all_previous_responses]

    async def solve_query(self, payload: QuerySolverInput):

        tools_to_use = [CODE_SEARCHER, ASK_USER_INPUT]

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
                previous_responses=await self.get_previous_messages(payload.session_id),
                tools=tools_to_use,
                stream=True,
                session_id=payload.session_id,
            )
            return llm_response

        elif payload.tool_use_response:
            llm_response = await llm_handler.submit_tool_use_response(
                session_id=payload.session_id,
                tool_use_response=ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name=payload.tool_use_response.tool_name,
                        tool_use_id=payload.tool_use_response.tool_use_id,
                        response=payload.tool_use_response.response,
                    )
                ),
                tools=tools_to_use,
                stream=True,
            )
            return llm_response

        else:
            raise ValueError("Invalid input")
