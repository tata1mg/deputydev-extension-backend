from typing import Any, Dict, Optional

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.analytics_events_dto import AnalyticsEventsData
from app.backend_common.repository.analytics_events.repository import AnalyticsEventsRepository
from app.backend_common.repository.message_sessions.repository import MessageSessionsRepository
from app.main.blueprints.deputy_dev.services.repository.extension_reviews.repository import ExtensionReviewsRepository
from app.main.blueprints.deputy_dev.services.repository.ide_reviews_comments.repository import IdeCommentRepository
from app.main.blueprints.one_dev.services.kafka.analytics_events.dataclasses.kafka_analytics_events import (
    KafkaAnalyticsEventMessage, EventTypes,
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

            user_team_id = None
            if analytics_event_message.event_type in [EventTypes.COMMENT_BOX_VIEW, EventTypes.FIX_WITH_DD]:
                comment_id = analytics_event_message.event_data.get('comment_id')
                if not comment_id:
                    raise ValueError(f"comment_id is required for event_type '{analytics_event_message.event_type}'")

                user_team_id = await self.get_user_team_id_from_comment_id(comment_id)
                if not user_team_id:
                    raise ValueError(f"Could not determine user_team_id from comment_id {comment_id}")
            else:

                message_session_dto = await MessageSessionsRepository.get_by_id(analytics_event_message.session_id)
                user_team_id = message_session_dto.user_team_id
                if not message_session_dto:
                    raise ValueError(f"Session with ID {analytics_event_message.session_id} not found.")

            return AnalyticsEventsData(
                **analytics_event_message.model_dump(mode="json"),
                user_team_id=user_team_id,
            )

        except Exception as ex:
            raise ValueError(f"Error processing error analytics event message: {str(ex)}")

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

    async def get_user_team_id_from_comment_id(self, comment_id: int) -> Optional[int]:
        """
        Get user_team_id by fetching comment details and then review details.
        Args:
            comment_id: The ID of the comment from event_data

        Returns:
            user_team_id if found, None otherwise
        """
        try:
            comment = await IdeCommentRepository.db_get(
                filters={"id": comment_id, "is_deleted": False},
                fetch_one=True
            )
            if not comment:
                raise ValueError(f"Comment with ID {comment_id} not found or deleted.")

            review = await ExtensionReviewsRepository.db_get(
                filters={"id": comment.review_id, "is_deleted": False},
                fetch_one=True
            )
            if not review:
                raise ValueError(f"Review with ID {comment.review_id} not found or deleted.")

            return review.user_team_id
        except Exception as ex:
            raise ValueError(f"Error fetching user_team_id from comment_id {comment_id}: {str(ex)}")
