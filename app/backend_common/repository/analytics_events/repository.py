import pytz

from app.backend_common.models.dao.postgres.analytics_events import AnalyticsEvents
from app.backend_common.models.dto.analytics_events_dto import (
    AnalyticsEventsData,
    AnalyticsEventsDTO,
)
from app.backend_common.repository.db import DB


class AnalyticsEventsRepository:
    @classmethod
    async def save_analytics_event(cls, analytics_events_dto: AnalyticsEventsData) -> AnalyticsEventsDTO:
        analytics_events_dto.timestamp = analytics_events_dto.timestamp.replace(tzinfo=pytz.UTC)
        payload = analytics_events_dto.model_dump(mode="json")
        row = await DB.insert_row(AnalyticsEvents, payload)
        return AnalyticsEventsDTO(
            id=row.id,
            session_id=row.session_id,
            event_type=row.event_type,
            client_version=row.client_version,
            client=row.client,
            timestamp=row.timestamp,
            user_team_id=row.user_team_id,
            event_data=row.event_data,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
