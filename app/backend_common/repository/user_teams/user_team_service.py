from typing import List, Union

from sanic.log import logger

from app.main.blueprints.deputy_dev.models.dao.postgres.user_teams import UserTeams
from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from app.backend_common.repository.db import DB


class UserTeamService:
    @classmethod
    async def db_get(cls, filters, fetch_one=False) -> Union[UserTeamDTO, List[UserTeamDTO]]:
        try:
            user_team_data = await DB.by_filters(model_name=UserTeams, where_clause=filters, fetch_one=fetch_one)
            if user_team_data and fetch_one:
                return UserTeamDTO(**user_team_data)
            elif user_team_data:
                return [UserTeamDTO(**user_team) for user_team in user_team_data]
        except Exception as ex:
            logger.error(
                "error occurred while fetching user_team details from db for user_team: {}, ex: {}".format(filters, ex)
            )
            raise ex

    @classmethod
    async def db_insert(cls, user_team_dto: UserTeamDTO):
        try:
            payload = user_team_dto.model_dump()
            del payload["id"]
            row = await DB.insert_row(UserTeams, payload)
            return row
        except Exception as ex:
            logger.error("not able to insert user_team details to db {} exception {}".format(user_team_dto.dict(), ex))
            raise ex

    @classmethod
    async def find_or_create(cls, team_id, user_id, role, is_owner, is_billable):
        user_team_dto = await cls.db_get(
            filters={"team_id": team_id, "user_id": user_id}, fetch_one=True
        )
        if not user_team_dto:
            user_team_data = {
                "team_id": team_id,
                "user_id": user_id,
                "role": role,
                "is_owner": is_owner,
                "is_billable": is_billable,
            }
            user_team_dto = await cls.db_insert(UserTeamDTO(**user_team_data))
        return {
            "id": user_team_dto.id,
        }