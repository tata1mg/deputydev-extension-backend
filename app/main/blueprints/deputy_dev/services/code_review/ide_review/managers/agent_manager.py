from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.main.blueprints.deputy_dev.models.agent_crud_params import AgentCreateParams, AgentUpdateParams
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository


class AgentManager:
    DEFAULT_AGENTS = [
        UserAgentDTO(
            agent_name="security",
            display_name="Security",
            is_custom_agent=False,
            objective="Detects insecure code patterns and flags potential vulnerabilities to help you write safer, more secure code.",
        ),
        UserAgentDTO(
            agent_name="code_communication",
            display_name="Documentation",
            is_custom_agent=False,
            objective="Responsibility of this agent is checking code_communication issues.",
            confidence_score=0.98,
        ),
        UserAgentDTO(
            agent_name="performance_optimisation",
            display_name="Performance Optimization",
            is_custom_agent=False,
            objective="Identifies inefficient code patterns and suggests optimizations to boost performance and reduce resource usage.",
        ),
        UserAgentDTO(
            agent_name="code_maintainability",
            display_name="Code Maintainability",
            is_custom_agent=False,
            objective="Analyzes code for maintainability issues and flags patterns that may hurt long-term readability, structure, or reuse.",
        ),
        UserAgentDTO(
            agent_name="error",
            display_name="Error",
            is_custom_agent=False,
            objective="Flags code patterns likely to cause runtime errors, helping you catch issues early and ship safer code.",
        ),
    ]

    AGENT_FIELDS = {"id", "agent_name", "custom_prompt", "is_custom_agent", "objective", "display_name"}

    async def create_agent(self, agent_params: AgentCreateParams) -> dict:
        """
        Create a new agent with the provided parameters.

        Args:
            agent_params (dict): Parameters for creating the agent.

        Returns:
            dict: The created agent's data.
        """
        # Implementation to create an agent
        agent = UserAgentDTO(
            agent_name=agent_params.agent_name,
            display_name=agent_params.name,
            user_team_id=agent_params.user_team_id,
            custom_prompt=agent_params.custom_prompt,
            is_custom_agent=True,
        )
        if agent.is_custom_agent and not agent.custom_prompt:
            raise BadRequestException("For custom agent custom prompt is required")
        agent = await UserAgentRepository.db_insert(agent)
        return agent.model_dump(mode="json", include=self.AGENT_FIELDS)

    async def update_agent(self, agent_params: AgentUpdateParams) -> dict:
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
            if not agent.custom_prompt:
                raise BadRequestException("For custom agent custom prompt is required")
            agent.display_name = agent_params.name

        updated_agent = await UserAgentRepository.db_update({"id": agent.id}, agent.model_dump(exclude_unset=True))
        return updated_agent.model_dump(mode="json", include=self.AGENT_FIELDS)

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

    @classmethod
    async def get_or_create_agents(cls, user_team_id: int) -> list:
        """
        Fetch all agents for a specific user team.

        Args:
            user_team_id (int): The ID of the user team.

        Returns:
            list[UserAgentDTO]: List of agents associated with the user team.
        """
        agent_fileter = {"user_team_id": user_team_id, "is_deleted": False}
        agents = await UserAgentRepository.db_get(filters=agent_fileter)
        if not agents:
            await UserAgentRepository.bulk_create_agents(cls.DEFAULT_AGENTS, user_team_id)
            agents = await UserAgentRepository.db_get(filters=agent_fileter)
        agents_response = [agent.model_dump(mode="json", include=cls.AGENT_FIELDS) for agent in agents]
        return agents_response
