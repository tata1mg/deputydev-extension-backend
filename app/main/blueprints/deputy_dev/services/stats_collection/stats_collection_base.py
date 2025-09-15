from abc import ABC
from typing import Any, Dict

from deputydev_core.exceptions.exceptions import RetryException
from deputydev_core.utils.context_vars import set_context_values
from sanic.log import logger

from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.backend_common.utils.app_utils import convert_to_datetime
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.utils import is_request_from_blocked_repo


class StatsCollectionBase(ABC):
    def __init__(self, payload: Dict[str, Any], vcs_type: str) -> None:
        self.payload = payload
        self.vcs_type = vcs_type
        self.repo_service = None
        self.workspace_dto = None
        self.repo_dto = None
        self.pr_dto = None
        self.stats_type = None

    async def save_to_db(self, extracted_payload: Dict[str, Any]) -> None:
        """implement Saving meta info to db"""
        raise NotImplementedError()

    async def revert(self) -> None:
        """Implement if any revert step is required"""
        pass

    async def process_event(self) -> None:
        try:
            if not self.check_serviceable_event():
                return
            await self.save_to_db(self.payload)
            logger.info(f"{self.stats_type} meta sync completed for payload {self.payload}")

        except RetryException as ex:
            raise ex

        except Exception as ex:  # noqa: BLE001
            await self.revert()
            logger.error(
                f"{self.stats_type} meta sync failed with for repo {self.payload.get('repo_name')}"
                f" and pr {self.payload.get('scm_pr_id')} exception {ex}"
            )
            raise RetryException(
                message=f"Unknown: {self.stats_type} meta sync failed with for repo "
                f"{self.payload.get('repo_name')}"
                f" and pr {self.payload.get('scm_pr_id')} exception {ex}"
            )

    async def get_pr_from_db(self, payload: Dict[str, Any]) -> None:
        self.payload["pr_created_at"] = (
            convert_to_datetime(self.payload["pr_created_at"]) if self.payload.get("pr_created_at") else None
        )
        self.workspace_dto = await WorkspaceService.find(
            scm_workspace_id=payload["scm_workspace_id"], scm=self.vcs_type
        )
        if not self.workspace_dto:
            raise RetryException(
                f"{self.stats_type} webhook failed for workspace {payload['scm_workspace_id']} due to"
                f"workspace not registered"
            )
        set_context_values(team_id=self.workspace_dto.team_id)
        self.repo_dto = await RepoRepository.db_get(
            filters=dict(scm_repo_id=payload["scm_repo_id"], workspace_id=self.workspace_dto.id), fetch_one=True
        )
        if not self.repo_dto:
            raise RetryException(
                f"{self.stats_type} webhook failed for repo {payload['repo_name']} due torepo not registered"
            )

        self.pr_dto = await PRService.find(
            filters={"scm_pr_id": payload["scm_pr_id"], "repo_id": self.repo_dto.id, "iteration": 1}
        )
        if not self.pr_dto:
            if (
                self.pr_created_after_onboarding_time()
            ):  # Failed case will also be handled as it will not have iteration value
                raise RetryException(f"PR: {self.payload['scm_pr_id']} not picked to be reviewed by Deputydev")

    async def generate_old_payload(self) -> None:
        """TODO deprecated method"""
        pass

    def check_serviceable_event(self) -> bool:
        return not is_request_from_blocked_repo(self.payload.get("repo_name"))

    def pr_created_after_onboarding_time(self) -> bool:
        """
        Check if PR is created after onboarding time of team.
         Returns:
             bool: True if pr created after onboarding time else False.
        """
        if not self.payload.get("pr_created_at") or self.payload.get("pr_created_at") > self.workspace_dto.created_at:
            return True
        return False
