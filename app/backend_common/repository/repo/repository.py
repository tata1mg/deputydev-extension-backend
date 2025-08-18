from typing import Dict, List, Union

from deputydev_core.utils.context_vars import get_context_value
from sanic.log import logger

from app.backend_common.models.dao.postgres.repos import Repos
from app.backend_common.models.dto.pr.base_pr import BasePrModel
from app.backend_common.models.dto.repo_dto import RepoDTO
from app.backend_common.repository.db import DB
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.backend_common.utils import app_utils


class RepoRepository:
    @classmethod
    async def db_get(cls, filters: Dict, fetch_one: bool = False) -> Union[RepoDTO, List[RepoDTO]]:
        try:
            repo_data = await DB.by_filters(model_name=Repos, where_clause=filters, fetch_one=fetch_one)
            if repo_data and fetch_one:
                return RepoDTO(**repo_data)
            elif repo_data:
                return [RepoDTO(**repo) for repo in repo_data]
        except Exception as ex:
            logger.error("error occurred while fetching repo details from db for repo: {}, ex: {}".format(filters, ex))
            raise ex

    @classmethod
    async def db_insert(cls, repo_dto: RepoDTO) -> RepoDTO:
        try:
            payload = repo_dto.dict()
            del payload["id"]
            row = await DB.insert_row(Repos, payload)
            return row
        except Exception as ex:
            logger.error("not able to insert repo details to db {} exception {}".format(repo_dto.dict(), ex))
            raise ex

    @classmethod
    async def find_or_create(cls, workspace_id: int, team_id: int, pr_model: BasePrModel) -> RepoDTO:
        repo_dto = await cls.db_get(
            filters={"scm_repo_id": pr_model.scm_repo_id(), "workspace_id": workspace_id}, fetch_one=True
        )
        if not repo_dto:
            repo_origin = get_context_value("repo_origin")
            repo_hash = app_utils.hash_sha256(repo_origin)
            repo_data = {
                "team_id": team_id,
                "scm": pr_model.scm_type(),
                "scm_repo_id": pr_model.scm_repo_id(),
                "name": pr_model.scm_repo_name(),
                "repo_hash": repo_hash,
                "workspace_id": workspace_id,
            }
            repo_dto = await RepoRepository.db_insert(RepoDTO(**repo_data))
        return repo_dto

    @classmethod
    async def find_or_create_with_workspace_id(cls, scm_workspace_id: str, pr_model: BasePrModel) -> RepoDTO:
        workspace_dto = await WorkspaceService.find(scm_workspace_id=scm_workspace_id, scm=pr_model.scm_type())
        repo_dto = await cls.find_or_create(workspace_dto.id, workspace_dto.team_id, pr_model)
        return repo_dto

    @classmethod
    async def find_or_create_extension_repo(cls, repo_name: str, repo_origin: str, team_id: int) -> RepoDTO:
        repo_hash = app_utils.hash_sha256(repo_origin)
        repo_dto = await cls.db_get(
            filters={"name": repo_name, "repo_hash": repo_hash, "team_id": team_id}, fetch_one=True
        )
        if not repo_dto:
            repo_data = {
                "name": repo_name,
                "repo_hash": repo_hash,
                "team_id": team_id,
            }
            repo_dto = await cls.db_insert(RepoDTO(**repo_data))
        return repo_dto
