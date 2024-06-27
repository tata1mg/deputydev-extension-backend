from app.common.services.sqs.base_subscriber import BaseSubscriber

from ..code_review.pr_review import CodeReviewManager


class GenaiSubscriber(BaseSubscriber):
    def get_queue_name(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("GENAI", {}).get("QUEUE_NAME", "")

    @property
    def event_handler(self):
        return CodeReviewManager
