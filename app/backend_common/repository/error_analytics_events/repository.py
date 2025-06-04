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
        cls, analytics_events_dto: ErrorAnalyticsEventsData
    ) -> ErrorAnalyticsEventsDTO:
        analytics_events_dto.timestamp = analytics_events_dto.timestamp.replace(
            tzinfo=pytz.UTC)
        payload = analytics_events_dto.model_dump(mode="json")
        row: ErrorAnalyticsEvents = await DB.insert_row(ErrorAnalyticsEvents, payload)
        return ErrorAnalyticsEventsDTO(
            id=row.id,
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
