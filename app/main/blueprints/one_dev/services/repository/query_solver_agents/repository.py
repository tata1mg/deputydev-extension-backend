from typing import List

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.one_dev.models.dao.postgres.query_solver_agents import QuerySolverAgent
from app.main.blueprints.one_dev.models.dto.query_solver_agents_dto import QuerySolverAgentsDTO


class QuerySolverAgentsRepository:
    @classmethod
    async def get_query_solver_agents(cls, status: str = "ACTIVE") -> List[QuerySolverAgentsDTO]:
        try:
            query_solver_agents = await DB.by_filters(
                model_name=QuerySolverAgent,
                where_clause={"status": status},
                fetch_one=False,
            )
            if not query_solver_agents:
                return None
            return [QuerySolverAgentsDTO(**agent) for agent in query_solver_agents]
        except Exception as ex:
            logger.error(f"error occurred while getting query_solver_agents in db for status : {status}, ex: {ex}")
            raise ex
