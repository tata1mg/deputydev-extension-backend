import pytz

from app.backend_common.models.dao.postgres.session_events import SessionEvents
from app.backend_common.models.dto.session_events_dto import SessionEventsDTO
from app.backend_common.repository.db import DB


class SessionEventsRepository:
    @classmethod
    async def db_insert(cls, session_events_dto: SessionEventsDTO) -> SessionEventsDTO:
        payload = session_events_dto.model_dump()
        payload["timestamp"] = payload["timestamp"].replace(tzinfo=pytz.UTC)
        row = await DB.insert_row(SessionEvents, payload)
        return row
