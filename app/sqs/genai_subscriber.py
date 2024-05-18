from app.managers.deputy_dev.code_review import CodeReviewManager

from .base_subscriber import BaseSubscriber


class GenaiSubscriber(BaseSubscriber):
    def get_queue_name(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("GENAI", {}).get("QUEUE_NAME", "")

    @property
    def event_handler(self):
        return CodeReviewManager
