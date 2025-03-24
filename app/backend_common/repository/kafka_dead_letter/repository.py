from app.backend_common.models.dao.postgres.kafka_dead_letter import FailedKafkaMessages
from app.backend_common.models.dto.session_events_dto import SessionEventsDTO
from app.backend_common.repository.db import DB
from typing import Dict


class KafkaDeadLetterRepository:
    @classmethod
    async def db_insert(cls, message: Dict) -> SessionEventsDTO:
        row = await DB.insert_row(FailedKafkaMessages, message)
        return row