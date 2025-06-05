from typing import Any, Dict, cast

from app.backend_common.models.dto.analytics_events_dto import AnalyticsEventsData
from app.backend_common.repository.analytics_events.repository import AnalyticsEventsRepository
from app.backend_common.repository.message_sessions.repository import MessageSessionsRepository
from deputydev_core.utils.app_logger import AppLogger

from app.main.blueprints.one_dev.services.kafka.analytics_events.dataclasses.kafka_analytics_events import (
    KafkaAnalyticsEventMessage,
)

from ..base_kafka_subscriber import BaseKafkaSubscriber


class AnalyticsEventSubscriber(BaseKafkaSubscriber):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config, config["KAFKA"]["SESSION_QUEUE"]["NAME"])

    async def _get_analytics_event_data_from_message(self, message: Dict[str, Any]) -> AnalyticsEventsData:
        """Extract and return AnalyticsEventsData from the message."""
        try:
            # try to parse message directly as AnalyticsEventsData
            analytics_event_message = KafkaAnalyticsEventMessage(**message)
            message_session_dto = await MessageSessionsRepository.get_by_id(analytics_event_message.session_id)
            if not message_session_dto:
                raise ValueError(f"Session with ID {analytics_event_message.session_id} not found.")

            return AnalyticsEventsData(
                **analytics_event_message.model_dump(mode="json"),
                user_team_id=message_session_dto.user_team_id,
            )

        except Exception:
            # TODO: This is for backward compatibility with old messages, can be removed once min supported extension version is 6.0.0
            # if parsing fails, the message can be in old format
            # in that case, we will extract the data manually
            message_session_dto = await MessageSessionsRepository.get_by_id(message["properties"]["session_id"])
            if not message_session_dto:
                raise ValueError(f"Session with ID {message['session_id']} not found.")

            return AnalyticsEventsData(
                session_id=message["properties"]["session_id"],
                event_type=cast(str, message["event"]).upper(),
                client_version=message_session_dto.client_version or "UNKNOWN",
                client=message_session_dto.client,
                timestamp=message["properties"]["timestamp"],
                user_team_id=message_session_dto.user_team_id,
                event_data={
                    "lines": message["properties"]["lines"],
                    "source": message["properties"].get("source", "UNKNOWN"),
                    "file_path": message["properties"]["file_path"],
                },
            )

    async def _process_message(self, message: Any) -> None:
        """Process and store session event messages in DB."""
        event_data = message.value
        try:
            analytics_event_data = await self._get_analytics_event_data_from_message(event_data)
            await AnalyticsEventsRepository.save_analytics_event(analytics_event_data)
        except Exception as _ex:
            AppLogger.log_error(
                f"Error processing analytics event message from Kafka: {str(_ex)}. Message: {str(event_data)}"
            )
            return
