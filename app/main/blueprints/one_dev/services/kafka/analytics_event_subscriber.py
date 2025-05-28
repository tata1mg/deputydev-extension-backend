from typing import Any

from app.backend_common.models.dto.analytics_events_dto import AnalyticsEventsData
from app.backend_common.repository.analytics_events.repository import AnalyticsEventsRepository

from .base_kafka_subscriber import BaseKafkaSubscriber


class AnalyticsEventSubscriber(BaseKafkaSubscriber):
    def __init__(self, config):
        super().__init__(config, config.get("KAFKA", {}).get("SESSION_QUEUE_NAME"))

    async def _process_message(self, message: Any) -> None:
        """Process and store session event messages in DB."""
        event_data = message.value
        analytics_event_data = AnalyticsEventsData(
            **event_data,
        )
        await AnalyticsEventsRepository.save_analytics_event(analytics_event_data)
