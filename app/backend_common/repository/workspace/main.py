from typing import Any, Dict, List, Optional, Union

from sanic.log import logger

from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.models.dto.workspace_dto import WorkspaceDTO
from app.backend_common.repository.db import DB


class WorkspaceService:
    @classmethod
    async def db_get(
        cls, filters: Dict[str, Any], fetch_one: bool = False
    ) -> Optional[Union[List[WorkspaceDTO], WorkspaceDTO]]:
        try:
            workspaces = await DB.by_filters(model_name=Workspaces, where_clause=filters, fetch_one=False)
            if workspaces and fetch_one:
                return WorkspaceDTO(**workspaces[0])
            elif workspaces:
                return [WorkspaceDTO(**workspace) for workspace in workspaces]
        except Exception as ex:  # noqa: BLE001
            logger.error(
                "error occurred while fetching workspace details from db for workspace filters : {}, ex: {}".format(
                    filters, ex
                )
            )
