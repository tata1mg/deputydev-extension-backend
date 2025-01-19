from typing import List, Union

from sanic.log import logger

from app.main.blueprints.deputy_dev.models.dao.postgres.users import Users
from app.backend_common.models.dto.user_dto import UserDTO
from app.backend_common.repository.db import DB


class UserService:
    @classmethod
    async def db_get(cls, filters, fetch_one=False) -> Union[UserDTO, List[UserDTO]]:
        try:
            user_data = await DB.by_filters(model_name=Users, where_clause=filters, fetch_one=fetch_one)
            if user_data and fetch_one:
                return UserDTO(**user_data)
            elif user_data:
                return [UserDTO(**user) for user in user_data]
        except Exception as ex:
            logger.error("error occurred while fetching user details from db for user: {}, ex: {}".format(filters, ex))
            raise ex

    @classmethod
    async def db_insert(cls, user_dto: UserDTO):
        try:
            payload = user_dto.model_dump()
            del payload["id"]
            row = await DB.insert_row(Users, payload)
            return row
        except Exception as ex:
            logger.error("not able to insert user details to db {} exception {}".format(user_dto.dict(), ex))
            raise ex

    @classmethod
    async def find_or_create(cls, name, email, org_name):
        user_dto = await cls.db_get(
            filters={"email": email}, fetch_one=True
        )
        if not user_dto:
            user_data = {
                "name": name,
                "email": email,
                "org_name": org_name,
            }
            user_dto = await cls.db_insert(UserDTO(**user_data))
        return {
            "id": user_dto.id,
        }
