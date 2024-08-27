from abc import ABC
from datetime import datetime

from sanic.log import logger
from torpedo import CONFIG

from app.common.exception import RetryException
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.workspace.workspace_service import (
    WorkspaceService,
)


class StatsCollectionBase(ABC):
    def __init__(self, payload, query_params):
        self.payload = payload
        self.vcs_type = query_params.get("vcs_type", VCSTypes.bitbucket.value)
        self.repo_service = None
        self.workspace_dto = None
        self.repo_dto = None
        self.pr_dto = None
        self.experiment_start_time = datetime.fromisoformat(CONFIG.config.get("EXPERIMENT_START_TIME"))
        self.stats_type = None

    def extract_payload(self):
        """Extract payload"""
        raise NotImplementedError()

    async def save_to_db(self, extracted_payload):
        """implement Saving meta info to db"""
        raise NotImplementedError()

    async def revert(self):
        """Implement if any revert step is required"""
        pass

    async def process_event(self) -> None:
        extracted_payload = {}
        try:
            extracted_payload = self.extract_payload()
            await self.save_to_db(extracted_payload)
            logger.info(f"{self.stats_type} meta sync completed for payload {extracted_payload}")

        except RetryException as ex:
            logger.error(
                f"{self.stats_type} meta sync failed with for repo {extracted_payload.get('repo_name')}"
                f" and pr {extracted_payload.get('scm_pr_id')} exception {ex}"
            )
            raise ex

        except Exception as ex:
            await self.revert()
            logger.error(
                f"{self.stats_type} meta sync failed with for repo {extracted_payload.get('repo_name')}"
                f" and pr {extracted_payload.get('scm_pr_id')} exception {ex}"
            )
            raise RetryException(
                message=f"Unknown: {self.stats_type} meta sync failed with for repo "
                f"{extracted_payload.get('repo_name')}"
                f" and pr {extracted_payload.get('scm_pr_id')} exception {ex}"
            )

    async def get_pr_from_db(self, payload):
        workspace_dto = await WorkspaceService.find(scm_workspace_id=payload["scm_workspace_id"], scm=self.vcs_type)
        if not workspace_dto:
            raise RetryException(
                f"{self.stats_type} webhook failed for workspace {payload['scm_workspace_id']} due to"
                f"workspace not registered"
            )

        self.repo_dto = await RepoService.find(scm_repo_id=payload["scm_repo_id"], workspace_id=workspace_dto.id)
        if not self.repo_dto:
            raise RetryException(
                f"{self.stats_type} webhook failed for repo {payload['repo_name']} due to" f"repo not registered"
            )

        self.pr_dto = await PRService.find(repo_id=self.repo_dto.id, scm_pr_id=payload["scm_pr_id"])
        if not self.pr_dto:
            if payload["pr_created_at"] > self.experiment_start_time:
                raise RetryException(
                    f"{self.stats_type} webhook failed for repo {payload['scm_repo_id']} due to"
                    f" pr review not started"
                )
