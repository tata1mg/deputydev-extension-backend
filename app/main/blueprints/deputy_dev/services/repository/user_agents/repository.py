from typing import List, Union, Optional
from sanic.log import logger
from app.main.blueprints.deputy_dev.models.dao.postgres.user_agents import UserAgents
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.backend_common.repository.db import DB


class UserAgentRepository:
    @classmethod
    async def db_get(cls, filters, fetch_one=False, order_by="agent_name") -> Union[UserAgentDTO, List[UserAgentDTO]]:
        try:
            agent_data = await DB.by_filters(
                model_name=UserAgents, where_clause=filters, fetch_one=fetch_one, order_by=order_by
            )
            if agent_data and fetch_one:
                return UserAgentDTO(**agent_data)
            elif agent_data:
                return [UserAgentDTO(**agent) for agent in agent_data]
        except Exception as ex:
            logger.error(f"Error fetching user agent: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, agent_dto: UserAgentDTO) -> UserAgentDTO:
        try:
            payload = agent_dto.dict()
            del payload["id"]
            row = await DB.insert_row(UserAgents, payload)
            row_dict = await row.to_dict()
            return UserAgentDTO(**row_dict)
        except Exception as ex:
            logger.error(f"Error inserting user agent: {agent_dto.dict()}, ex: {ex}")
            raise ex

    @classmethod
    async def db_update(cls, filters, payload) -> Optional[UserAgentDTO]:
        try:
            payload.pop("id", None)
            await UserAgents.filter(**filters).update(**payload)
            updated = await cls.db_get(filters, fetch_one=True)
            return updated
        except Exception as ex:
            logger.error(f"Error updating user agent: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def update_agent(cls, filters, payload):
        try:
            await UserAgents.filter(**filters).update(**payload)
            return
        except Exception as ex:
            logger.error(f"Error updating user agent: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_delete(cls, agent_id) -> None:
        try:
            await UserAgents.filter(id=agent_id).update(is_deleted=True)
        except Exception as ex:
            logger.error(f"Error soft deleting user agent: {agent_id}, ex: {ex}")
            raise ex

    @classmethod
    async def bulk_create_agents(cls, agents: List[UserAgentDTO], user_team_id: int) -> None:
        """
        Bulk create agents in the database.

        Args:
            agents (List[UserAgentDTO]): List of UserAgentDTO objects to be created.
            user_team_id: int - The ID of the user team to which these agents belong.
        """
        user_agents = []
        for agent in agents:
            agent.user_team_id = user_team_id
            agent_dict = agent.model_dump(exclude={"id", "created_at", "updated_at"})
            user_agents.append(UserAgents(**agent_dict))
        await UserAgents.bulk_create(user_agents)