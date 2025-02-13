from app.backend_common.services.llm.handler import LLMHandler
from app.common.constants.constants import LLModels, PromptFeatures
from app.common.services.prompt.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    QuerySolverInput,
)
from app.main.blueprints.one_dev.services.query_solver.tools.code_searcher import CODE_SEARCHER
from app.main.blueprints.one_dev.services.query_solver.tools.diff_applicator import DIFF_APPLICATOR


class QuerySolver:
    async def solve_query(self, payload: QuerySolverInput):
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.CODE_QUERY_SOLVER,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={"query": payload.query, "relevant_chunks": payload.relevant_chunks},
        )

        llm_response = await LLMHandler(
            prompt_handler=prompt, tools=[DIFF_APPLICATOR, CODE_SEARCHER], stream=True
        ).get_llm_response_data(previous_responses=[])
        return llm_response
