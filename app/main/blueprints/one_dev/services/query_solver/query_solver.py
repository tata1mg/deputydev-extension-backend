from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    ToolUseResponseContent,
    ToolUseResponseData,
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
from app.main.blueprints.one_dev.services.query_solver.tools.diff_applicator import (
    DIFF_APPLICATOR,
)

from .prompts.factory import PromptFeatureFactory


class QuerySolver:
    async def solve_query(self, payload: QuerySolverInput):

        tools_to_use = [CODE_SEARCHER, ASK_USER_INPUT]
        if payload.write_mode:
            tools_to_use.append(DIFF_APPLICATOR)

        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)

        if payload.query:
            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures.CODE_QUERY_SOLVER,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                prompt_vars={"query": payload.query, "relevant_chunks": payload.relevant_chunks},
                previous_responses=[],
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
