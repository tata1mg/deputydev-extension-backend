from abc import ABC
from typing import List, Type


from app.main.blueprints.one_dev.services.query_solver.agents.tasks.base_query_solver_agent_task import (
    BaseQuerySolverAgentTask,
)


class BaseQuerySolverAgent(ABC):
    """
    Base class for query solver agents.
    """

    # this needs to be overridden by the subclass
    agent_name: str = "BaseQuerySolverAgent"
    description: str = "Base Query Solver Agent"

    tasks: List[Type[BaseQuerySolverAgentTask]] = []

    def get_all_task_descriptions(self) -> List[str]:
        """
        Get descriptions of all tasks.
        """
        return [task.description for task in self.tasks]
