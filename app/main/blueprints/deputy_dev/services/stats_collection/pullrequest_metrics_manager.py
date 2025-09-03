from typing import Any, Dict

from pydantic import ValidationError
from sanic.log import logger

from app.backend_common.exception import RetryException
from app.backend_common.utils.app_utils import convert_to_datetime
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.constants.constants import (
    MetaStatCollectionTypes,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.models.pr_close_request import PRCloseRequest
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_base import (
    StatsCollectionBase,
)
from app.main.blueprints.deputy_dev.services.webhook.pullrequest_close_webhook import (
    PullRequestCloseWebhook,
)


class PullRequestMetricsManager(StatsCollectionBase):
    def __init__(self, payload: Dict[str, Any], vcs_type: str) -> None:
        super().__init__(payload, vcs_type)
        self.stats_type = MetaStatCollectionTypes.PR_CLOSE.value
        self.sqs_message_retention_time = CONFIG.config.get("SQS", {}).get("MESSAGE_RETENTION_TIME_SEC", 0)

    def validate_payload(self) -> bool:
        """
        Validates the PRCloseRequest payload and raises BadRequestException if validation fails.
        """
        try:
            # backward compatibility handling
            self.handle_old_keys()
            PRCloseRequest(**self.payload)
            return True
        except ValidationError as ex:
            logger.error(f"Invalid pr close request with error {ex}")
            return False

    def handle_old_keys(self) -> None:
        if "repo_id" in self.payload:
            self.payload["scm_repo_id"] = self.payload.pop("repo_id")

    async def process_event(self) -> None:
        logger.info(f"PR close payload: {self.payload}")
        if not self.check_serviceable_event():
            return
        await self.get_pr_from_db(self.payload)
        if not self.pr_dto:  # PR is raised before onboarding time
            return
        self.payload["pr_closed_at"] = convert_to_datetime(self.payload["pr_closed_at"])

        if self.pr_dto.review_status == PrStatusTypes.IN_PROGRESS.value:
            raise RetryException(f"PR: {self.payload['scm_pr_id']} is still in progress to be reviewed by Deputydev")

        if self.pr_dto.review_status not in [PrStatusTypes.COMPLETED.value, PrStatusTypes.REJECTED_EXPERIMENT.value]:
            # For not completed or not rejected experiment we will just be updating the pr state of both experiments and pull request
            # table without updating comment count.

            await PRService.db_update(
                payload={
                    "pr_state": self.payload["pr_state"],
                    "scm_close_time": self.payload["pr_closed_at"],
                },
                filters={"scm_pr_id": self.pr_dto.scm_pr_id, "repo_id": self.pr_dto.repo_id},
            )
            return

        close_cycle_time = await self.calculate_pr_close_cycle_time()

        await self.post_pr_close_processing(close_cycle_time)

    async def post_pr_close_processing(self, close_cycle_time: int) -> None:
        await PRService.db_update(
            payload={
                "scm_close_time": self.payload["pr_closed_at"],
                "pr_state": self.payload["pr_state"],
            },
            filters={"scm_pr_id": self.pr_dto.scm_pr_id, "repo_id": self.pr_dto.repo_id},
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

    async def calculate_pr_close_cycle_time(self) -> int:
        """
        Calculates the stats_collection cycle time from the provided payload and VCS type, then stores it.
        """
        pr_created_at = self.payload["pr_created_at"]
        pr_closed_at = self.payload["pr_closed_at"]

        created_time_epoch = int(pr_created_at.timestamp())
        pr_close_time_epoch = int(pr_closed_at.timestamp())

        cycle_time_seconds = pr_close_time_epoch - created_time_epoch

        return cycle_time_seconds

    async def generate_old_payload(self) -> None:
        self.payload = await PullRequestCloseWebhook.parse_payload(self.payload)
        self.payload = self.payload.dict()
