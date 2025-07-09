from typing import List, Union, Optional
from sanic.log import logger
from app.main.blueprints.deputy_dev.models.dao.postgres.user_agents import UserAgent
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.backend_common.repository.db import DB


class UserAgentRepository:
    @classmethod
    async def db_get(cls, filters, fetch_one=False, order_by=None) -> Union[UserAgentDTO, List[UserAgentDTO]]:
        try:
            agent_data = await DB.by_filters(
                model_name=UserAgent, where_clause=filters, fetch_one=fetch_one, order_by=order_by
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
            row = await DB.insert_row(UserAgent, payload)
            return UserAgentDTO(**row)
        except Exception as ex:
            logger.error(f"Error inserting user agent: {agent_dto.dict()}, ex: {ex}")
            raise ex

    @classmethod
    async def db_update(cls, filters, payload) -> Optional[UserAgentDTO]:
        try:
            await DB.update_by_filters(UserAgent, filters, payload)
            updated = await cls.db_get(filters, fetch_one=True)
            return updated
        except Exception as ex:
            logger.error(f"Error updating user agent: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_delete(cls, filters) -> None:
        try:
            await DB.delete_by_filters(UserAgent, filters)
        except Exception as ex:
            logger.error(f"Error deleting user agent: {filters}, ex: {ex}")
            raise ex
