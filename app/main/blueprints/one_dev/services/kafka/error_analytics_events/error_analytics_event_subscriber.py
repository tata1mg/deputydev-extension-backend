from typing import Any, Dict, Optional

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.error_analytics_events_dto import ErrorAnalyticsEventsData
from app.backend_common.repository.error_analytics_events.repository import ErrorAnalyticsEventsRepository
from app.backend_common.repository.message_sessions.repository import MessageSessionsRepository
from app.main.blueprints.one_dev.services.kafka.error_analytics_events.dataclasses.kafka_error_analytics_events import (
    KafkaErrorAnalyticsEventMessage,
)

from ..base_kafka_subscriber import BaseKafkaSubscriber


class ErrorAnalyticsEventSubscriber(BaseKafkaSubscriber):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config, config["KAFKA"]["ERROR_QUEUE"]["NAME"])

    async def _get_analytics_event_data_from_message(
        self, message: Dict[str, Any]
    ) -> Optional[ErrorAnalyticsEventsData]:
        """Extract and return ErrorAnalyticsEventsData from the message."""
        try:
            error_analytics_event_message = KafkaErrorAnalyticsEventMessage(**message)
            if error_analytics_event_message.error_id:
                if await ErrorAnalyticsEventsRepository.error_id_exists(error_analytics_event_message.error_id):
                    AppLogger.log_warn(
                        f"Duplicate event with ID '{error_analytics_event_message.error_id}' received. Skipping."
                    )
                    return None
            session_id: Optional[int] = getattr(error_analytics_event_message, "session_id", None)

            user_team_id = None
            if session_id:
                message_session_dto = await MessageSessionsRepository.get_by_id(session_id)
                if not message_session_dto:
                    raise ValueError(f"Session with ID {session_id} not found.")
                user_team_id = message_session_dto.user_team_id

            return ErrorAnalyticsEventsData(
                **error_analytics_event_message.model_dump(mode="json"),
                user_team_id=user_team_id,
            )

        except Exception as ex:  # noqa: BLE001
            raise ValueError(f"Error processing error analytics event message: {str(ex)}")

    async def _process_message(self, message: Any) -> None:
        """Process and store session event messages in DB."""
        event_data = message.value
        try:
            error_analytics_event_data = await self._get_analytics_event_data_from_message(event_data)
            if error_analytics_event_data is None:
                AppLogger.log_warn(f"Skipping duplicate or invalid analytics event: {event_data}")
                return
            await ErrorAnalyticsEventsRepository.save_error_analytics_event(error_analytics_event_data)
        except Exception as ex:  # noqa: BLE001
            AppLogger.log_error(
                f"Error processing error analytics event message from Kafka: {str(ex)}. Message: {str(event_data)}"
            )
