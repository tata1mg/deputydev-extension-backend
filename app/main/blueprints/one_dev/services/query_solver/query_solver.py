from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
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

        if payload.query:
            prompt = PromptFeatureFactory.get_prompt(
                prompt_feature=PromptFeatures.CODE_QUERY_SOLVER,
                model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
                init_params={"query": payload.query, "relevant_chunks": payload.relevant_chunks},
            )
            llm_response = await LLMHandler(prompt_handler=prompt, tools=tools_to_use, stream=True).start_llm_query(
                previous_responses=[]
            )
            return llm_response

        elif payload.tool_use_response:
            llm_response = await LLMHandler(tools=tools_to_use, stream=True).submit_tool_use_response(
                session_id=payload.session_id,
                tool_use_response=ToolUseResponseData(
                    tool_name=payload.tool_use_response.tool_name,
                    tool_use_id=payload.tool_use_response.tool_use_id,
                    response=payload.tool_use_response.response,
                ),
            )
            return llm_response
