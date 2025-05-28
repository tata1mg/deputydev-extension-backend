import pytz

from app.backend_common.models.dao.postgres.pixel_events import AnalyticsEvents
from app.backend_common.models.dto.pixel_events_dto import (
    PixelEventsData,
    PixelEventsDTO,
)
from app.backend_common.repository.db import DB


class PixelEventsRepository:
    @classmethod
    async def db_insert(cls, pixel_events_dto: PixelEventsData) -> PixelEventsDTO:
        pixel_events_dto.timestamp = pixel_events_dto.timestamp.replace(tzinfo=pytz.UTC)
        payload = pixel_events_dto.model_dump(mode="json")
        row = await DB.insert_row(AnalyticsEvents, payload)
        return row
