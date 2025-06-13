import pytz

from app.backend_common.models.dao.postgres.error_analytics_events import ErrorAnalyticsEvents
from app.backend_common.models.dto.error_analytics_events_dto import (
    ErrorAnalyticsEventsData,
    ErrorAnalyticsEventsDTO,
)
from app.backend_common.repository.db import DB


class ErrorAnalyticsEventsRepository:
    @classmethod
    async def save_error_analytics_event(
        cls, error_analytics_events_dto: ErrorAnalyticsEventsData
    ) -> ErrorAnalyticsEventsDTO:
        error_analytics_events_dto.timestamp = error_analytics_events_dto.timestamp.replace(tzinfo=pytz.UTC)
        payload = error_analytics_events_dto.model_dump(mode="json")
        row = await DB.insert_row(ErrorAnalyticsEvents, payload)
        return ErrorAnalyticsEventsDTO(
            id=row.id,
            error_id=row.error_id,
            user_email=row.user_email,
            error_type=row.error_type,
            error_data=row.error_data,
            repo_name=row.repo_name,
            error_source=row.error_source,
            client_version=row.client_version,
            timestamp=row.timestamp,
            user_team_id=row.user_team_id,
            session_id=row.session_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @classmethod
    async def error_id_exists(cls, error_id: str) -> bool:
        count = await DB.count_by_filters(model_name=ErrorAnalyticsEvents, filters={"error_id": error_id})
        return count > 0
