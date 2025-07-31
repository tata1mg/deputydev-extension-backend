from typing import List, Optional, Union

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.user_agent_comment_mapping import UserAgentCommentMapping
from app.main.blueprints.deputy_dev.models.dto.user_agent_comment_mapping_dto import UserAgentCommentMappingDTO


class UserAgentCommentMappingRepository:
    @classmethod
    async def db_get(
        cls, filters, fetch_one=False, order_by=None
    ) -> Union[UserAgentCommentMappingDTO, List[UserAgentCommentMappingDTO]]:
        try:
            data = await DB.by_filters(
                model_name=UserAgentCommentMapping, where_clause=filters, fetch_one=fetch_one, order_by=order_by
            )
            if data and fetch_one:
                return UserAgentCommentMappingDTO(**data)
            elif data:
                return [UserAgentCommentMappingDTO(**item) for item in data]
        except Exception as ex:
            logger.error(f"Error fetching user agent comment mapping: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, mapping_dto: UserAgentCommentMappingDTO) -> UserAgentCommentMappingDTO:
        try:
            payload = mapping_dto.dict()
            del payload["id"]
            row = await DB.insert_row(UserAgentCommentMapping, payload)
            row_dict = await row.to_dict()
            return UserAgentCommentMappingDTO(**row_dict)
        except Exception as ex:
            logger.error(f"Error inserting user agent comment mapping: {mapping_dto.dict()}, ex: {ex}")
            raise ex

    @classmethod
    async def db_update(cls, filters, payload) -> Optional[UserAgentCommentMappingDTO]:
        try:
            await DB.update_by_filters(UserAgentCommentMapping, filters, payload)
            updated = await cls.db_get(filters, fetch_one=True)
            return updated
        except Exception as ex:
            logger.error(f"Error updating user agent comment mapping: {filters}, ex: {ex}")
            raise ex
