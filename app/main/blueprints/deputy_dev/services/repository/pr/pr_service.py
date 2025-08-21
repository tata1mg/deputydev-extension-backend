from typing import Any, Dict, List, Optional

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import get_context_value
from sanic.log import logger
from tortoise.exceptions import IntegrityError

from app.backend_common.models.dao.postgres.repos import Repos
from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.models.dto.pr.base_pr import BasePrModel
from app.backend_common.models.dto.repo_dto import RepoDTO
from app.backend_common.repository.db import DB
from app.backend_common.repository.repo.repository import RepoRepository
from app.main.blueprints.deputy_dev.constants.constants import PrStatusTypes
from app.main.blueprints.deputy_dev.models.dao.postgres import PullRequests
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO


class PRService:
    @classmethod
    async def db_insert(cls, pr_dto: PullRequestDTO) -> Optional[PullRequestDTO]:
        try:
            payload = pr_dto.dict()
            del payload["id"]
            row = await DB.insert_row(PullRequests, payload)
            if row:
                pr_dto = PullRequestDTO(**await row.to_dict())
                return pr_dto
        except IntegrityError as e:
            AppLogger.log_warn(f"Integrity error creating PR: {e}")
            return None
        except Exception as ex:
            logger.error("not able to insert pr details {} exception {}".format(pr_dto.dict(), ex))
            raise ex

    @classmethod
    async def db_update(cls, payload: Dict[str, Any], filters: Dict[str, Any]) -> Optional[PullRequestDTO]:
        try:
            await DB.update_by_filters(None, PullRequests, payload, where_clause=filters)
            row = await cls.db_get(filters)
            return row
        except Exception as ex:
            logger.error("not able to update pr details {}  exception {}".format(payload, ex))
            raise ex

    @classmethod
    async def db_get(cls, filters: Dict[str, Any], order_by: Optional[List[str]] = None) -> Optional[PullRequestDTO]:
        try:
            pr_info = await DB.by_filters(
                model_name=PullRequests, where_clause=filters, limit=1, fetch_one=True, order_by=order_by
            )
            if pr_info:
                return PullRequestDTO(**pr_info)
        except Exception as ex:  # noqa: BLE001
            logger.error(
                "error occurred while fetching pr details from db for pr filters : {}, ex: {}".format(filters, ex)
            )

    @classmethod
    async def db_get_count(cls, filters: Dict[str, Any]) -> int:
        count = await DB.count_by_filters(PullRequests, filters)
        return count

    @classmethod
    async def find_or_create(
        cls, pr_model: BasePrModel, pr_status: str, pr_commits: List[str]
    ) -> Optional[PullRequestDTO]:
        pr_dto = None
        team_id, workspace_id = get_context_value("team_id"), get_context_value("workspace_id")
        if workspace_id:
            repo_dto = await RepoRepository.find_or_create(
                workspace_id=workspace_id, team_id=team_id, pr_model=pr_model
            )

        #  Pick Failed PR incase not reviewed for current commit_ids
        failed_pr_dto = await cls.find_failed_pr(pr_model, repo_dto)

        if failed_pr_dto:  # Update the review_state and commit ids of failed entry
            failed_update_payload = {
                "commit_id": pr_model.commit_id(),
                "destination_commit_id": pr_model.destination_branch_commit(),
                "review_status": pr_status,
                "destination_branch": pr_model.destination_branch(),
            }

            try:
                pr_dto = await PRService.db_update(payload=failed_update_payload, filters={"id": failed_pr_dto.id})
            except IntegrityError as ex:  # Case where Other entry exists with same source and destination commit
                AppLogger.log_warn(f"Integrity error updating PR: {ex}")
                return
        else:
            pr_model.meta_info = {
                "review_status": pr_status,
                "team_id": repo_dto.team_id,
                "workspace_id": repo_dto.workspace_id,
                "repo_id": repo_dto.id,
            }
            pr_dto = PullRequestDTO(**pr_model.get_pr_info())
            pr_dto.pr_state = pr_model.scm_state()
            pr_dto = await PRService.db_insert(pr_dto)
        return pr_dto

    @classmethod
    async def find_reviewed_pr(cls, pr_model: BasePrModel, repo_dto: RepoDTO) -> Optional[PullRequestDTO]:
        """Find a last reviewed PR on that destination branch"""
        filters = {
            "scm_pr_id": pr_model.scm_pr_id(),
            "repo_id": repo_dto.id,
            "destination_branch": pr_model.destination_branch(),
            "review_status__in": [
                PrStatusTypes.COMPLETED.value,
                PrStatusTypes.REJECTED_LARGE_SIZE.value,
                PrStatusTypes.REJECTED_NO_DIFF.value,
                PrStatusTypes.REJECTED_CLONING_FAILED_WITH_128.value,
                PrStatusTypes.REJECTED_INVALID_REQUEST.value,
            ],
        }
        return await PRService.find(filters=filters, order_by=["-updated_at"])

    @classmethod
    async def find_failed_pr(cls, pr_model: BasePrModel, repo_dto: RepoDTO) -> Optional[PullRequestDTO]:
        """Find earliest failed PR of scm_pr_id."""
        filters = {
            "scm_pr_id": pr_model.scm_pr_id(),
            "repo_id": repo_dto.id,
            "review_status": PrStatusTypes.FAILED.value,
        }
        return await PRService.find(filters=filters, order_by=["-updated_at"])

    @classmethod
    async def find(cls, filters: Dict[str, Any], order_by: Optional[List[str]] = None) -> List[PullRequestDTO]:
        return await PRService.db_get(filters=filters, order_by=order_by)

    @classmethod
    async def get_bulk_prs_by_filter(cls, query_params: Dict[str, Any]) -> List[PullRequestDTO]:
        all_prs = await DB.raw_sql(
            "SELECT * FROM pull_requests where id>={} and id<{} and scm_close_time is null and (pr_state='OPEN' or pr_state='APPROVED')".format(
                query_params.get("start"), query_params.get("end")
            )
        )
        return all_prs

    @classmethod
    def get_completed_pr_filters(cls, pr_dto: PullRequestDTO) -> Dict[str, Any]:
        """
        Get filters for completed PR records
        """
        return {
            "scm_pr_id": pr_dto.scm_pr_id,
            "repo_id": pr_dto.repo_id,
            "review_status__in": [
                PrStatusTypes.COMPLETED.value,
                PrStatusTypes.REJECTED_LARGE_SIZE.value,
                PrStatusTypes.REJECTED_NO_DIFF.value,
                PrStatusTypes.REJECTED_CLONING_FAILED_WITH_128.value,
                PrStatusTypes.REJECTED_INVALID_REQUEST.value,
                PrStatusTypes.REJECTED_ALREADY_MERGED.value,
                PrStatusTypes.REJECTED_ALREADY_DECLINED.value,
            ],
        }

    @classmethod
    async def get_completed_pr_count(cls, pr_dto: PullRequestDTO) -> int:
        """
        Get count of completed PRs for given PR DTO

        Args:
            pr_dto: PullRequest DTO

        Returns:
            int: Count of completed PRs
        """
        filters = cls.get_completed_pr_filters(pr_dto)
        return await cls.db_get_count(filters)

    @classmethod
    async def fetch_pr(
        cls, scm_workspace_id: int, repo_name: str, scm: str, scm_pr_id: int
    ) -> Optional[PullRequestDTO]:
        workspace = await Workspaces.get_or_none(scm_workspace_id=scm_workspace_id, scm=scm)
        repo = await Repos.get_or_none(workspace_id=workspace.id, name=repo_name)
        if repo:
            pr = await PullRequests.get_or_none(repo_id=repo.id, scm_pr_id=scm_pr_id)
            return pr
