from prompts.factory import PromptFeatureFactory

from app.backend_common.services.llm.dataclasses.main import LLModels
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


class QuerySolver:
    async def solve_query(self, payload: QuerySolverInput):
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.CODE_QUERY_SOLVER,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={"query": payload.query, "relevant_chunks": payload.relevant_chunks},
        )

        tools_to_use = [CODE_SEARCHER, ASK_USER_INPUT]
        if payload.write_mode:
            tools_to_use.append(DIFF_APPLICATOR)

        llm_response = await LLMHandler(prompt_handler=prompt, tools=tools_to_use, stream=True).get_llm_response_data(
            previous_responses=[]
        )
        return llm_response
