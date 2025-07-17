from typing import Any, Dict, List, Optional

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import NonStreamingParsedLLMCallResponse
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.query_solver.agents.base_query_solver_agent import (
    QuerySolverAgent,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import DetailedDirectoryItem, DetailedFocusItem
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures


class QuerySolverAgentSelector:
    """
    Class to select the appropriate query solver agent based on the input.
    """

    def __init__(
        self,
        user_query: str,
        focus_items: List[DetailedFocusItem],
        directory_items: List[DetailedDirectoryItem],
        last_agent: Optional[str],
        all_agents: List[QuerySolverAgent],
        llm_handler: LLMHandler[PromptFeatures],
        session_id: int,
        default_agent: Optional[QuerySolverAgent] = None,
    ) -> None:
        # Initialize with the user query.
        self.user_query = user_query
        self.focus_items = focus_items
        self.directory_items = directory_items
        self.all_agents = all_agents
        self.llm_handler = llm_handler
        self.session_id = session_id
        self.default_agent = default_agent
        self.last_agent = last_agent

    async def select_agent(self) -> Optional[QuerySolverAgent]:
        """
        Select the appropriate agent for the user query.
        """

        # Here we would typically use the LLM handler to analyze the user query
        # and determine which task is most appropriate.
        # For simplicity, we will return a placeholder agent name.
        # return the agent that is most appropriate for the user query

        if not self.all_agents:
            return self.default_agent or None

        prompt_vars: Dict[str, Any] = {
            "query": self.user_query,
            "focus_items": self.focus_items,
            "directory_items": self.directory_items,
            "intents": [
                {
                    "name": agent.agent_name,
                    "description": agent.agent_description,
                }
                for agent in self.all_agents
            ],
            "last_agent": self.last_agent,
        }

        selected_intent = await self.llm_handler.start_llm_query(
            prompt_vars=prompt_vars,
            session_id=self.session_id,
            llm_model=LLModels.GEMINI_2_POINT_5_FLASH,
            prompt_feature=PromptFeatures.INTENT_SELECTOR,
        )

        if not isinstance(selected_intent, NonStreamingParsedLLMCallResponse):
            raise ValueError("Invalid response from LLM. Expected NonStreamingParsedLLMCallResponse.")

        agent = next(
            (
                agent
                for agent in self.all_agents
                if agent.agent_name == selected_intent.parsed_content[0]["intent_name"]
            ),
            None,
        )

        if agent:
            return agent

        return self.default_agent or None
