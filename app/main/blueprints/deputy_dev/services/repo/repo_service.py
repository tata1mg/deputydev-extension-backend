from sanic.log import logger

from app.main.blueprints.deputy_dev.models.dao import Repos
from app.main.blueprints.deputy_dev.models.dto.pr.base_pr import BasePrModel
from app.main.blueprints.deputy_dev.models.dto.repo_dto import RepoDTO
from app.main.blueprints.deputy_dev.services.db.db import DB


class RepoService:
    @classmethod
    async def db_get(cls, filters) -> RepoDTO:
        try:
            repo_data = await DB.by_filters(model_name=Repos, where_clause=filters, limit=1, fetch_one=True)
            if repo_data:
                return RepoDTO(**repo_data)
        except Exception as ex:
            logger.error("error occurred while fetching repo details from db for repo: {}, ex: {}".format(filters, ex))
            raise ex

    @classmethod
    async def db_insert(cls, repo_dto: RepoDTO):
        try:
            payload = repo_dto.dict()
            del payload["id"]
            row = await DB.insert_row(Repos, payload)
            return row
        except Exception as ex:
            logger.error("not able to insert repo details to db {} exception {}".format(repo_dto.dict(), ex))
            raise ex

    @classmethod
    async def find_or_create(cls, workspace_id, team_id, pr_model: BasePrModel):
        repo_dto = await cls.find(workspace_id=workspace_id, scm_repo_id=pr_model.scm_repo_id())
        if not repo_dto:
            repo_data = {
                "team_id": team_id,
                "scm": pr_model.scm_type(),
                "scm_repo_id": pr_model.scm_repo_id(),
                "name": pr_model.scm_repo_name(),
                "workspace_id": workspace_id,
            }
            repo_dto = await RepoService.db_insert(RepoDTO(**repo_data))
        return repo_dto

    @classmethod
    async def find(cls, workspace_id, scm_repo_id):
        return await RepoService.db_get(filters={"scm_repo_id": scm_repo_id, "workspace_id": workspace_id})
