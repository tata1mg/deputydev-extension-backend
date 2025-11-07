import asyncio
from typing import List

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.utils.app_logger import AppLogger

from app.main.blueprints.one_dev.models.dto.agent_chats import AgentChatDTO
from app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent import QuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.agent_selector.agent_selector import QuerySolverAgentSelector
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import QuerySolverInput
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.one_dev.services.repository.query_solver_agents.repository import QuerySolverAgentsRepository


class AgentManager:
    """Handle agent-related operations for QuerySolver."""

    def get_default_agent(self) -> QuerySolverAgent:
        """Return the default query solver agent."""
        return QuerySolverAgent(
            agent_name="DEFAULT_QUERY_SOLVER_AGENT",
            agent_description="This is the default query solver agent that should used when no specific agent is solves the purpose",
        )

    async def generate_dynamic_query_solver_agents(self) -> List[QuerySolverAgent]:
        """Generate list of available query solver agents."""
        # get all the intents from the database
        default_agent = self.get_default_agent()
        all_agents = await QuerySolverAgentsRepository.get_query_solver_agents()
        if not all_agents:
            return [default_agent]

        # create a list of agent classes based on the data from the database
        agent_classes: List[QuerySolverAgent] = []
        for agent_data in all_agents:
            agent_class = QuerySolverAgent(
                agent_name=agent_data.name,
                agent_description=agent_data.description,
                allowed_tools=agent_data.allowed_first_party_tools,
                prompt_intent=agent_data.prompt_intent,
            )
            agent_classes.append(agent_class)

        return agent_classes + [default_agent]

    def get_agent_instance_by_name(self, agent_name: str, all_agents: List[QuerySolverAgent]) -> QuerySolverAgent:
        """
        Get the agent instance by its name.
        """
        agent = next((agent for agent in all_agents if agent.agent_name == agent_name), None)
        if not agent:
            raise ValueError(f"Agent with name {agent_name} not found")
        return agent

    async def get_query_solver_agent_instance(
        self,
        payload: QuerySolverInput,
        llm_handler: LLMHandler[PromptFeatures],
        previous_agent_chats: List[AgentChatDTO],
    ) -> QuerySolverAgent:
        """Get the appropriate query solver agent instance for the payload."""
        all_agents = await self.generate_dynamic_query_solver_agents()  # this will have default agent as well
        agent_instance: QuerySolverAgent

        if not all_agents:
            raise Exception("No query solver agents found in the system")

        default_agent = self.get_default_agent()
        if payload.query:
            agent_selector = QuerySolverAgentSelector(
                user_query=payload.query,
                focus_items=payload.focus_items,
                last_agent=previous_agent_chats[-1].metadata.get("agent_name")
                if previous_agent_chats and previous_agent_chats[-1].metadata
                else None,
                all_agents=all_agents,
                llm_handler=llm_handler,
                session_id=payload.session_id,
            )
            try:
                agent_instance = await asyncio.wait_for(agent_selector.select_agent(), timeout=5)
            except asyncio.TimeoutError:
                AppLogger.log_info("Agent selection timed out, using default query solver agent instead.")
                agent_instance = default_agent
        else:
            agent_name = (
                previous_agent_chats[-1].metadata.get("agent_name")
                if previous_agent_chats and previous_agent_chats[-1].metadata
                else None
            )
            agent_instance: QuerySolverAgent = self.get_agent_instance_by_name(
                agent_name=agent_name or "DEFAULT_QUERY_SOLVER_AGENT",
                all_agents=all_agents,
            )
        return agent_instance
