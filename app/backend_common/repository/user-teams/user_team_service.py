from typing import List, Union

from sanic.log import logger

from app.backend_common.models.dao.postgres.user_teams import UserTeams
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
