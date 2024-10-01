from datetime import datetime, timezone

from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG

from app.common.exception import RetryException
from app.common.utils.app_utils import convert_to_datetime
from app.main.blueprints.deputy_dev.constants.constants import PrStatusTypes
from app.main.blueprints.deputy_dev.models.pr_close_request import PRCloseRequest
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_base import (
    StatsCollectionBase,
)
from app.main.blueprints.deputy_dev.services.webhook.pullrequest_close_webhook import (
    PullRequestCloseWebhook,
)
from app.main.blueprints.deputy_dev.services.workspace.workspace_service import (
    WorkspaceService,
)
from app.main.blueprints.deputy_dev.utils import get_vcs_auth_handler


class PullRequestMetricsManager(StatsCollectionBase):
    def __init__(self, payload, query_params):
        super().__init__(payload, query_params)

        self.sqs_message_retention_time = CONFIG.config.get("SQS", {}).get("MESSAGE_RETENTION_TIME_SEC", 0)

    def validate_payload(self):
        """
        Validates the PRCloseRequest payload and raises BadRequestException if validation fails.
        """
        try:
            PRCloseRequest(**self.payload)
            return True
        except ValidationError as ex:
            logger.error(f"Invalid pr close request with error {ex}")
            return False

    async def process_event(self):
        logger.info(f"PR close paylod: {self.payload}")
        await self.initialize_repo_service()
        await self.initialize_workspace_and_repo_dto()
        await self.initialize_pr_dto()
        self.payload["pr_created_at"] = convert_to_datetime(self.payload["pr_created_at"])
        self.payload["pr_closed_at"] = convert_to_datetime(self.payload["pr_closed_at"])

        if not self.pr_dto:
            if self.payload["pr_created_at"] > self.experiment_start_time:
                raise RetryException(f"PR: {self.payload['pr_id']} not picked to be reviewed by Deputydev")
            else:
                return

        pr_time_since_creation = (
            datetime.now(timezone.utc) - self.pr_dto.scm_creation_time.astimezone(timezone.utc)
        ).total_seconds()

        if (
            self.pr_dto.review_status == PrStatusTypes.FAILED.value
            and pr_time_since_creation < self.sqs_message_retention_time
        ):
            raise RetryException(
                f"PR: {self.payload['pr_id']} is in sqs and still have a chance to be reviewed by Deputydev"
            )

        if self.pr_dto.review_status == PrStatusTypes.IN_PROGRESS.value:
            raise RetryException(f"PR: {self.payload['pr_id']} is still in progress to be reviewed by Deputydev")

        if self.pr_dto.review_status not in [PrStatusTypes.COMPLETED.value, PrStatusTypes.REJECTED_EXPERIMENT.value]:
            # For not completed or not rejected experiment we will just be updating the pr state of both experiments and pull request
            # table without updating comment count.
            await PRService.db_update(
                payload={
                    "pr_state": self.payload["pr_state"],
                    "scm_close_time": self.payload["pr_closed_at"],
                },
                filters={"repo_id": self.repo_dto.id, "scm_pr_id": self.payload["pr_id"]},
            )
            return

        close_cycle_time = await self.calculate_pr_close_cycle_time()

        await self.post_pr_close_processing(close_cycle_time)

    async def initialize_pr_dto(self):
        """
        Initializes the PR DTO.
        """
        self.pr_dto = await PRService.db_get(
            {
                "repo_id": self.repo_dto.id,
                "workspace_id": self.workspace_dto.id,
                "scm_pr_id": self.payload["pr_id"],
            }
        )

    async def initialize_workspace_and_repo_dto(self):
        """
        Initializes the workspace and repository DTOs.
        """
        pr_model = self.repo_service.pr_model()
        self.workspace_dto = await WorkspaceService.find(
            scm=pr_model.scm_type(),
            scm_workspace_id=pr_model.scm_workspace_id(),
        )
        if not self.workspace_dto:
            raise RetryException(f"Workspace not found in DB: SCM Workspace ID : {pr_model.scm_workspace_id()}")
        self.repo_dto = await RepoService.find(scm_repo_id=pr_model.scm_repo_id(), workspace_id=self.workspace_dto.id)
        if not self.repo_dto:
            raise RetryException(
                f"PR: {self.payload['pr_id']} not picked to be reviewed by Deputydev. Reason: Repository does not exist in our DB."
            )

    async def initialize_repo_service(self):
        """
        Retrieves the repository instance based on the given VCS type and payload.
        """
        repo_name = self.payload.get("repo_name")
        pr_id = self.payload.get("pr_id")
        workspace = self.payload.get("workspace")
        scm_workspace_id = self.payload.get("workspace_id")
        repo_id = self.payload.get("repo_id")
        workspace_slug = self.payload.get("workspace_slug")
        auth_handler = await get_vcs_auth_handler(scm_workspace_id, self.vcs_type)
        self.repo_service = await RepoFactory.repo(
            vcs_type=self.vcs_type,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace=workspace,
            workspace_id=scm_workspace_id,
            workspace_slug=workspace_slug,
            repo_id=repo_id,
            auth_handler=auth_handler,
        )

    async def post_pr_close_processing(self, close_cycle_time):

        await PRService.db_update(
            payload={
                "scm_close_time": self.payload["pr_closed_at"],
                "pr_state": self.payload["pr_state"],
            },
            filters={"repo_id": self.repo_dto.id, "scm_pr_id": self.payload["pr_id"]},
        )
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={
                    "scm_close_time": self.payload["pr_closed_at"],
                    "close_time_in_sec": close_cycle_time,
                    "pr_state": self.payload["pr_state"],
                },
                filters={"pr_id": self.pr_dto.id},
            )

    async def calculate_pr_close_cycle_time(self):
        """
        Calculates the stats_collection cycle time from the provided payload and VCS type, then stores it.
        """
        pr_created_at = self.payload["pr_created_at"]
        pr_closed_at = self.payload["pr_closed_at"]

        created_time_epoch = int(pr_created_at.timestamp())
        pr_close_time_epoch = int(pr_closed_at.timestamp())

        cycle_time_seconds = pr_close_time_epoch - created_time_epoch

        return cycle_time_seconds

    async def generate_old_payload(self):
        self.payload = await PullRequestCloseWebhook.parse_payload(self.payload, self.vcs_type)
        self.payload = self.payload.dict()
