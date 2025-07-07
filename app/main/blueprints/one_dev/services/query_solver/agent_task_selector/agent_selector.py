from typing import List, Type

from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.query_solver.agents.base_query_solver_agent_task import (
    BaseQuerySolverAgent,
)


class QuerySolverAgentSelector:
    """
    Class to select the appropriate query solver agent based on the input.
    """

    def __init__(self, user_query: str, all_agents: List[BaseQuerySolverAgent]) -> None:
        # Initialize with the user query.
        self.user_query = user_query
        self.llm_handler = LLMHandler()
        self.all_agents = all_agents

    def select_agent(self) -> Type[BaseQuerySolverAgent]:
        """
        Select the appropriate agent for the user query.
        """

        # Here we would typically use the LLM handler to analyze the user query
        # and determine which task is most appropriate.
        # For simplicity, we will return a placeholder task name.
        # return the agent task that is most appropriate for the user query
        task_name = self.llm_handler.get_task_name_from_query(self.user_query)

        if not task_name:
            # have a default agent here
            raise ValueError("No appropriate task found for the given user query.")

        return task_name
