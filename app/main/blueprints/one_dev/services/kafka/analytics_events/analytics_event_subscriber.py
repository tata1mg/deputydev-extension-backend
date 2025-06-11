from typing import Any, Dict, Optional

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

    async def _get_analytics_event_data_from_message(self, message: Dict[str, Any]) -> Optional[AnalyticsEventsData]:
        """Extract and return AnalyticsEventsData from the message."""
        try:
            # try to parse message directly as AnalyticsEventsData
            analytics_event_message = KafkaAnalyticsEventMessage(**message)
            if analytics_event_message.event_id:
                if await AnalyticsEventsRepository.event_id_exists(analytics_event_message.event_id):
                    AppLogger.log_warn(
                        f"Duplicate event with ID '{analytics_event_message.event_id}' received. Skipping."
                    )
                    return None
            message_session_dto = await MessageSessionsRepository.get_by_id(analytics_event_message.session_id)
            if not message_session_dto:
                raise ValueError(f"Session with ID {analytics_event_message.session_id} not found.")

            return AnalyticsEventsData(
                **analytics_event_message.model_dump(mode="json"),
                user_team_id=message_session_dto.user_team_id,
            )

        except Exception as ex:
            raise ValueError(
                f"Error processing error analytics event message: {str(ex)}")

    async def _process_message(self, message: Any) -> None:
        """Process and store session event messages in DB."""
        event_data = message.value
        try:
            analytics_event_data = await self._get_analytics_event_data_from_message(event_data)
            if analytics_event_data is None:
                AppLogger.log_warn(f"Skipping duplicate or invalid analytics event: {event_data}")
                return
            await AnalyticsEventsRepository.save_analytics_event(analytics_event_data)
        except Exception as _ex:
            AppLogger.log_error(
                f"Error processing analytics event message from Kafka: {str(_ex)}. Message: {str(event_data)}"
            )
            return
