from typing import List, Union

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_review_agent_status import IdeReviewAgentStatus
from app.main.blueprints.deputy_dev.models.dto.review_agent_status_dto import ReviewAgentStatusDTO
from deputydev_core.utils.app_logger import AppLogger


class ReviewAgentStatusRepository:
    @classmethod
    async def db_insert(cls, agent_status: ReviewAgentStatusDTO):
        """Insert a new agent status record."""
        try:
            payload = agent_status.dict()
            del payload["id"]
            row = await DB.insert_row(IdeReviewAgentStatus, payload)
            row_dict = await row.to_dict()
            return ReviewAgentStatusDTO(**row_dict)
        except Exception as ex:
            AppLogger.log_error(f"Error inserting agent status: {agent_status}, ex: {ex}")
            raise ex

    @classmethod
    async def db_get(
        cls, filters, fetch_one=False, order_by=None
    ) -> Union[ReviewAgentStatusDTO, List[ReviewAgentStatusDTO]]:
        try:
            agent_status_data = await DB.by_filters(
                model_name=IdeReviewAgentStatus, where_clause=filters, fetch_one=fetch_one, order_by=order_by
            )
            if agent_status_data and fetch_one:
                return ReviewAgentStatusDTO(**agent_status_data)
            elif agent_status_data:
                return [ReviewAgentStatusDTO(**status) for status in agent_status_data]
        except Exception as ex:
            AppLogger.log_error(f"Error fetching agent status: {filters}, ex: {ex}")
            raise ex
