from typing import Any, Dict

from pydantic import ValidationError
from sanic.log import logger

from app.backend_common.utils.app_utils import convert_to_datetime
from app.main.blueprints.deputy_dev.constants.constants import MetaStatCollectionTypes
from app.main.blueprints.deputy_dev.models.pr_approval_request import PRApprovalRequest
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_base import (
    StatsCollectionBase,
)
from app.main.blueprints.deputy_dev.services.webhook.pr_approval_webhook import (
    PRApprovalWebhook,
)


class PRApprovalTimeManager(StatsCollectionBase):
    def __init__(self, payload: Dict[str, Any], vcs_type: str) -> None:
        super().__init__(payload, vcs_type)
        self.stats_type = MetaStatCollectionTypes.PR_APPROVAL_TIME.value

    def validate_payload(self) -> bool:
        """
        Validates the PRCloseRequest payload and raises BadRequestException if validation fails.
        """
        try:
            PRApprovalRequest(**self.payload)
            return True
        except ValidationError as ex:
            logger.error(f"Invalid pr approval request with error {ex}")
            return False

    async def save_to_db(self, payload: Dict[str, Any]) -> None:
        await self.get_pr_from_db(payload)
        if not self.pr_dto:  # PR is raised before onboarding time
            return

        await PRService.db_update(
            payload={"scm_approval_time": convert_to_datetime(payload["scm_approval_time"])},
            filters={"scm_pr_id": self.pr_dto.scm_pr_id, "repo_id": self.pr_dto.repo_id},
        )

    async def generate_old_payload(self) -> None:
        self.payload = await PRApprovalWebhook.parse_payload(self.payload)
        self.payload = self.payload.dict()
