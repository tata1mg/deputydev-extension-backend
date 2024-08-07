from app.common.services.sqs.base_subscriber import BaseSubscriber
from app.main.blueprints.deputy_dev.services.stats_collection.pullrequest_metrics_manager import (
    PullRequestMetricsManager,
)


class MetaSubscriber(BaseSubscriber):
    def get_queue_name(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("METASYNC", {}).get("QUEUE_NAME", "")

    @property
    def event_handler(self):
        return PullRequestMetricsManager
