from app.main.blueprints.deputy_dev.models.agent_crud_params import AgentParams
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository


class AgentManager:
    async def create_agent(self, agent_params: AgentParams) -> dict:
        """
        Create a new agent with the provided parameters.

        Args:
            agent_params (dict): Parameters for creating the agent.

        Returns:
            dict: The created agent's data.
        """
        # Implementation to create an agent
        agent = UserAgentDTO(
            agent_name=agent_params.name,
            display_name=agent_params.name,
            user_team_id=agent_params.user_team_id,
            custom_prompt=agent_params.custom_prompt,
            is_custom_agent=True
        )
        agent = await UserAgentRepository.db_insert(agent)
        return agent.model_dump(mode="json", include={"id", "agent_name", "custom_prompt"})

    async def update_agent(self, agent_params: AgentParams) -> dict:
        """
        Update an existing agent with the provided parameters.
        Args:
            agent_params:

        Returns:

        """
        db_agent = await UserAgentRepository.db_get({"id": agent_params.id}, fetch_one=True)
        agent = UserAgentDTO(
            id=agent_params.id,
            custom_prompt=agent_params.custom_prompt,
        )
        if db_agent.is_custom_agent:
            agent.agent_name = agent_params.name

        updated_agent = await UserAgentRepository.db_update({"id": agent.id}, agent.model_dump(exclude_unset=True))
        return updated_agent.model_dump(mode="json", include={"id", "agent_name", "custom_prompt"})

    async def delete_agent(self, agent_id: int) -> dict:
        """
        Delete an agent by its ID.

        Args:
            agent_id (int): The ID of the agent to delete.

        Returns:
            dict: Confirmation of deletion.
        """
        await UserAgentRepository.db_delete(agent_id)
        return {"message": "Agent deleted successfully."}