from pydantic import ValidationError
from sanic.log import logger

from app.main.blueprints.deputy_dev.constants.constants import MetaStatCollectionTypes
from app.main.blueprints.deputy_dev.models.human_comment_request import (
    HumanCommentRequest,
)
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_base import (
    StatsCollectionBase,
)
from app.main.blueprints.deputy_dev.services.webhook.human_comment_webhook import (
    HumanCommentWebhook,
)


class HumanCommentCollectionManager(StatsCollectionBase):
    def __init__(self, payload, vcs_type):
        super().__init__(payload, vcs_type)
        self.scm_pr_id = None
        self.is_human_count_incremented = False
        self.stats_type = MetaStatCollectionTypes.HUMAN_COMMENT.value
        self.scm_pr_id = payload.get("scm_pr_id")

    def validate_payload(self):
        """
        Validates the PRCloseRequest payload and raises BadRequestException if validation fails.
        """
        try:
            HumanCommentRequest(**self.payload)
            return True
        except ValidationError as ex:
            logger.error(f"Invalid human comment request with error {ex}")
            return False

    async def save_to_db(self, payload):
        await self.get_pr_from_db(payload)
        if not self.pr_dto:  # PR is raised before onboarding time
            return
        if ExperimentService.is_eligible_for_experiment():
            self.is_human_count_incremented = await ExperimentService.increment_human_comment_count(
                scm_pr_id=self.scm_pr_id, repo_id=self.repo_dto.id
            )

    async def revert(self):
        if self.repo_dto and self.is_human_count_incremented:
            await ExperimentService.decrement_human_comment_count(scm_pr_id=self.scm_pr_id, repo_id=self.repo_dto.id)

    async def generate_old_payload(self):
        self.payload = await HumanCommentWebhook.parse_payload(self.payload)
        if not self.payload:
            return
        self.payload = self.payload.dict()
        self.scm_pr_id = self.payload.get("scm_pr_id")
