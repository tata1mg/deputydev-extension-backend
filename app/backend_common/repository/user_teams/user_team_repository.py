from typing import Any, Dict, List, Union

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dao.postgres.user_teams import UserTeams
from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from app.backend_common.repository.db import DB


class UserTeamRepository:
    @classmethod
    async def db_get(
        cls, filters: Dict[str, Any], fetch_one: bool = False
    ) -> Union[UserTeamDTO, List[UserTeamDTO]] | None:
        try:
            user_team_data = await DB.by_filters(model_name=UserTeams, where_clause=filters, fetch_one=fetch_one)
            if user_team_data and fetch_one:
                return UserTeamDTO(**user_team_data)
            elif user_team_data:
                return [UserTeamDTO(**user_team) for user_team in user_team_data]
        except Exception as ex:
            AppLogger.log_error(
                "error occurred while fetching user_team details from db for user_team: {}, ex: {}".format(filters, ex)
            )
            raise ex

    @classmethod
    async def db_insert(cls, user_team_dto: UserTeamDTO) -> UserTeamDTO:
        try:
            payload = user_team_dto.model_dump()
            del payload["id"]
            row = await DB.insert_row(UserTeams, payload)
            return row
        except Exception as ex:
            AppLogger.log_error(
                "not able to insert user_team details to db {} exception {}".format(user_team_dto.dict(), ex)
            )
            raise ex
