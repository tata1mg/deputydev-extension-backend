from sanic.log import logger

from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.models.dto.workspace_dto import WorkspaceDTO
from app.backend_common.repository.db import DB


class WorkspaceService:
    @classmethod
    async def db_get(cls, filters: dict) -> WorkspaceDTO:
        try:
            workspace_data = await DB.by_filters(model_name=Workspaces, where_clause=filters, limit=1, fetch_one=True)
            if workspace_data:
                return WorkspaceDTO(**workspace_data)
        except Exception as ex:
            logger.error(
                "error occurred while fetching workspace details from db for workspace : {}, ex: {}".format(filters, ex)
            )

    @classmethod
    async def find(cls, scm_workspace_id, scm) -> WorkspaceDTO:
        return await WorkspaceService.db_get(filters={"scm_workspace_id": scm_workspace_id, "scm": scm})
