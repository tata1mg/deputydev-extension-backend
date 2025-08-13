from typing import Any, Dict, List, Union

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dao.postgres.users import Users
from app.backend_common.models.dto.user_dto import UserDTO
from app.backend_common.repository.db import DB


class UserRepository:
    @classmethod
    async def db_get(cls, filters: Dict[str, Any], fetch_one: bool = False) -> Union[UserDTO, List[UserDTO]] | None:
        try:
            user_data = await DB.by_filters(model_name=Users, where_clause=filters, fetch_one=fetch_one)
            if user_data and fetch_one:
                return UserDTO(**user_data)
            elif user_data:
                return [UserDTO(**user) for user in user_data]
        except Exception as ex:
            AppLogger.log_error(
                "error occurred while fetching user details from db for user: {}, ex: {}".format(filters, ex)
            )
            raise ex

    @classmethod
    async def db_insert(cls, user_dto: UserDTO) -> UserDTO:
        try:
            payload = user_dto.model_dump()
            del payload["id"]
            row = await DB.insert_row(Users, payload)
            return row
        except Exception as ex:
            AppLogger.log_error("not able to insert user details to db {} exception {}".format(user_dto.dict(), ex))
            raise ex
