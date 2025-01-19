from typing import List, Union

from sanic.log import logger

from app.backend_common.models.dao.postgres.teams import Teams
from app.backend_common.models.dto.team_dto import TeamDTO
from app.backend_common.repository.db import DB


class TeamService:
    @classmethod
    async def db_get(cls, filters, fetch_one=False) -> Union[TeamDTO, List[TeamDTO]]:
        try:
            team_data = await DB.by_filters(model_name=Teams, where_clause=filters, fetch_one=fetch_one)
            if team_data and fetch_one:
                return TeamDTO(**team_data)
            elif team_data:
                return [TeamDTO(**team) for team in team_data]
        except Exception as ex:
            logger.error("error occurred while fetching team details from db for team: {}, ex: {}".format(filters, ex))
            raise ex
