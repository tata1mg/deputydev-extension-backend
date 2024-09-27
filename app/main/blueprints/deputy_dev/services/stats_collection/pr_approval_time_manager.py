from pydantic import ValidationError
from sanic.log import logger

from app.common.utils.app_utils import convert_to_datetime
from app.main.blueprints.deputy_dev.models.pr_approval_request import PRApprovalRequest
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_base import (
    StatsCollectionBase,
)


class PRApprovalTimeManager(StatsCollectionBase):
    def __init__(self, payload, query_params):
        super().__init__(payload, query_params)

    def validate_payload(self):
        """
        Validates the PRCloseRequest payload and raises BadRequestException if validation fails.
        """
        try:
            PRApprovalRequest(**self.payload)
            return True
        except ValidationError as ex:
            logger.error(f"Invalid pr approval request with error {ex}")
            return False

    async def save_to_db(self, payload):
        await self.get_pr_from_db(payload)
        await PRService.db_update(
            payload={"scm_approval_time": convert_to_datetime(payload["scm_approval_time"])},
            filters={"id": self.pr_dto.id},
        )
