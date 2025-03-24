from sanic.log import logger

from app.backend_common.models.dto.session_events_dto import SessionEventsData, SessionEventsDTO
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.repository.session_events.repository import (
    SessionEventsRepository,
)
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)

from .base_kafka_subscriber import BaseKafkaSubscriber


class SessionEventSubscriber(BaseKafkaSubscriber):
    def __init__(self, config):
        super().__init__(config, config.get("KAFKA", {}).get("SESSION_QUEUE_NAME"))

    async def _process_message(self, message):
        """Process and store session event messages in DB."""
        event_data = message.value
        session_event_data = SessionEventsData(**event_data)
        message_session_dto = await  MessageSessionsRepository.get_by_id(session_event_data.session_id)
        user_teams_dto = await UserTeamRepository.db_get(filters={"id": message_session_dto.id}, fetch_one=True)
        session_event_data.user_id = user_teams_dto.user_id
        session_event_data.team_id = user_teams_dto.team_id

        await SessionEventsRepository.db_insert(session_event_data)