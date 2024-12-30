from typing import Optional

from sanic.log import logger
from tortoise.exceptions import IntegrityError

from app.main.blueprints.deputy_dev.constants.constants import PrStatusTypes
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.models.dao import PullRequests, Repos, Workspaces
from app.main.blueprints.deputy_dev.models.dto.pr.base_pr import BasePrModel
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.db.db import DB
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)


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
    async def db_update(cls, payload, filters):
        try:
            await DB.update_by_filters(None, PullRequests, payload, where_clause=filters)
            row = await cls.db_get(filters)
            return row
        except Exception as ex:
            logger.error("not able to update pr details {}  exception {}".format(payload, ex))
            raise ex

    @classmethod
    async def db_get(cls, filters: dict, order_by=None) -> PullRequestDTO:
        try:
            pr_info = await DB.by_filters(
                model_name=PullRequests, where_clause=filters, limit=1, fetch_one=True, order_by=order_by
            )
            if pr_info:
                return PullRequestDTO(**pr_info)
        except Exception as ex:
            logger.error(
                "error occurred while fetching pr details from db for " "pr filters : {}, ex: {}".format(filters, ex)
            )

    @classmethod
    async def db_get_count(cls, filters: dict) -> int:
        count = await DB.count_by_filters(PullRequests, filters)
        return count

    @classmethod
    async def find_or_create(cls, pr_model: BasePrModel, pr_status, pr_commits) -> Optional[PullRequestDTO]:
        pr_dto = None
        team_id, workspace_id = get_context_value("team_id"), get_context_value("workspace_id")
        if workspace_id:
            repo_dto = await RepoService.find_or_create(workspace_id=workspace_id, team_id=team_id, pr_model=pr_model)

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
    async def find_reviewed_pr(cls, pr_model: BasePrModel, repo_dto) -> Optional[PullRequestDTO]:
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
    async def find_failed_pr(cls, pr_model: BasePrModel, repo_dto) -> Optional[PullRequestDTO]:
        """Find earliest failed PR of scm_pr_id."""
        filters = {
            "scm_pr_id": pr_model.scm_pr_id(),
            "repo_id": repo_dto.id,
            "review_status": PrStatusTypes.FAILED.value,
        }
        return await PRService.find(filters=filters, order_by=["-updated_at"])

    @classmethod
    async def find(cls, filters, order_by=None):
        return await PRService.db_get(filters=filters, order_by=order_by)

    @classmethod
    async def get_bulk_prs_by_filter(cls, query_params):
        all_prs = await DB.raw_sql(
            "SELECT * FROM pull_requests where id>={} and id<{} and scm_close_time is null and (pr_state='OPEN' or pr_state='APPROVED')".format(
                query_params.get("start"), query_params.get("end")
            )
        )
        return all_prs

    @classmethod
    async def update_meta_info(cls, id, loc_changed, token_count):
        # This function is not getting used can remove
        # TODO: PRDIFF Need to check usage of this function as we dropping pr_diff_tokens
        pr_dto = await PRService.db_get({"id": id})
        if pr_dto:
            meta_info = pr_dto.meta_info or {}
            meta_info.pop("pr_diff_tokens", None)
            meta_info.setdefault("tokens", {})["pr_diff_tokens"] = token_count
            await PRService.db_update(payload={"meta_info": meta_info, "loc_changed": loc_changed}, filters={"id": id})

    @classmethod
    def get_completed_pr_filters(cls, pr_dto: PullRequestDTO) -> dict:
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
    async def fetch_pr(cls, scm_workspace_id, repo_name, scm, scm_pr_id):
        workspace = await Workspaces.get_or_none(scm_workspace_id=scm_workspace_id, scm=scm)
        repo = await Repos.get_or_none(workspace_id=workspace.id, name=repo_name)
        if repo:
            pr = await PullRequests.get_or_none(repo_id=repo.id, scm_pr_id=scm_pr_id)
            return pr
