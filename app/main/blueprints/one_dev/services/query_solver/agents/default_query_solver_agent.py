from typing import Type

from app.main.blueprints.one_dev.services.query_solver.agents.base_query_solver_agent import QuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.factory import (
    CodeQuerySolverPromptFactory,
)
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory


class DefaultQuerySolverAgent(QuerySolverAgent):
    """
    Base class for query solver agents.
    This class should be extended by specific query solver agents.
    """

    prompt_factory: Type[BaseFeaturePromptFactory] = CodeQuerySolverPromptFactory

    def __init__(self) -> None:
        super().__init__(
            agent_name="DEFAULT_QUERY_SOLVER_AGENT",
            agent_description="This is the default query solver agent that should used when no specific agent is defined",
        )


DefaultQuerySolverAgentInstance = DefaultQuerySolverAgent()
