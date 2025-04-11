from typing import Any, Dict, Optional

from app.backend_common.models.dto.pixel_events_dto import PixelEventsData
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.repository.pixel_events.repository import PixelEventsRepository
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)

from .base_kafka_subscriber import BaseKafkaSubscriber


class PixelEventSubscriber(BaseKafkaSubscriber):
    def __init__(self, config):
        super().__init__(config, config.get("KAFKA", {}).get("SESSION_QUEUE_NAME"))

    async def _process_message(self, message: Any) -> None:
        """Process and store session event messages in DB."""
        event_data = message.value
        parsed_event_data = self.parse_event_data(event_data)
        message_session_dto = await MessageSessionsRepository.get_by_id(parsed_event_data["session_id"])
        user_teams_dto = await UserTeamRepository.db_get(
            filters={"id": message_session_dto.user_team_id}, fetch_one=True
        )
        pixel_event_data = PixelEventsData(
            **parsed_event_data,
            user_id=user_teams_dto.user_id,
            team_id=user_teams_dto.team_id,
            client_version=message_session_dto.client_version,
            client=message_session_dto.client,
        )

        await PixelEventsRepository.db_insert(pixel_event_data)

    def parse_event_data(self, event_data: Dict[str, Any]) -> dict[str, Optional[Any]]:

        event_id = event_data["anonymous_id"]
        event_type = event_data["event"]
        session_id = event_data["properties"]["session_id"]
        lines = event_data["properties"]["lines"]
        file_path = event_data["properties"]["file_path"]
        timestamp = event_data["properties"]["timestamp"]
        source = event_data["properties"].get("source", None)

        return {
            "event_id": event_id,
            "event_type": event_type,
            "session_id": session_id,
            "lines": lines,
            "file_path": file_path,
            "timestamp": timestamp,
            "source": source,
        }
