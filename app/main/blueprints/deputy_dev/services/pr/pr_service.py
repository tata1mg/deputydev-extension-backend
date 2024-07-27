from sanic.log import logger

from app.main.blueprints.deputy_dev.models.dao import PullRequests
from app.main.blueprints.deputy_dev.models.dto.pr.base_pr import BasePrModel
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.db.db import DB
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.workspace.workspace_service import (
    WorkspaceService,
)


class PRService:
    @classmethod
    async def db_insert(cls, pr_dto: PullRequestDTO) -> PullRequestDTO:
        try:
            payload = pr_dto.dict()
            del payload["id"]
            row = await DB.insert_row(PullRequests, payload)
            if row:
                pr_dto = PullRequestDTO(**await row.to_dict())
                return pr_dto
        except Exception as ex:
            logger.error("not able to insert pr details {} exception {}".format(pr_dto.dict(), ex))
            raise ex

    @classmethod
    async def db_update(cls, payload, filters):
        try:
            row = await DB.update_by_filters(None, PullRequests, payload, where_clause=filters)
            return row
        except Exception as ex:
            logger.error("not able to update pr details {}  exception {}".format(payload, ex))
            raise ex

    @classmethod
    async def db_get(cls, filters: dict) -> PullRequestDTO:
        try:
            pr_info = await DB.by_filters(model_name=PullRequests, where_clause=filters, limit=1, fetch_one=True)
            if pr_info:
                return PullRequestDTO(**pr_info)
        except Exception as ex:
            logger.error(
                "error occurred while fetching pr details from db for " "pr filters : {}, ex: {}".format(filters, ex)
            )

    @classmethod
    async def find_or_create(cls, pr_model: BasePrModel, pr_status) -> PullRequestDTO:
        pr_dto = None
        workspace_dto = await WorkspaceService.find(
            scm_workspace_id=pr_model.scm_workspace_id(), scm=pr_model.scm_type()
        )
        if workspace_dto:
            repo_dto = await RepoService.find_or_create(
                workspace_id=workspace_dto.id, organisation_id=workspace_dto.organisation_info.id, pr_model=pr_model
            )

            if repo_dto:
                pr_dto = await PRService.find(repo_id=repo_dto.id, scm_pr_id=pr_model.scm_pr_id())
                if not pr_dto:
                    pr_model.meta_info = {
                        "review_status": pr_status,
                        "organisation_id": repo_dto.organisation_id,
                        "workspace_id": repo_dto.workspace_id,
                        "repo_id": repo_dto.id,
                    }
                    pr_dto = PullRequestDTO(**pr_model.get_pr_info())
                    pr_dto = await PRService.db_insert(pr_dto)
        return pr_dto

    @classmethod
    async def find(cls, repo_id, scm_pr_id):
        return await PRService.db_get({"scm_pr_id": scm_pr_id, "repo_id": repo_id})
