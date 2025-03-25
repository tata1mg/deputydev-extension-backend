import pytz

from app.backend_common.models.dao.postgres.pixel_events import PixelEvents
from app.backend_common.models.dto.pixel_events_dto import (
    PixelEventsData,
    PixelEventsDTO,
)
from app.backend_common.repository.db import DB


class PixelEventsRepository:
    @classmethod
    async def db_insert(cls, pixel_events_dto: PixelEventsData) -> PixelEventsDTO:
        payload = pixel_events_dto.model_dump()
        payload["timestamp"] = payload["timestamp"].replace(tzinfo=pytz.UTC)
        row = await DB.insert_row(PixelEvents, payload)
        return row
