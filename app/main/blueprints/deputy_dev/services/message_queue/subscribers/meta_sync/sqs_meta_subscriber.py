from app.main.blueprints.deputy_dev.services.message_queue.subscribers.base.base_subscriber import (
    BaseSubscriber,
)
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_factory import (
    StatsCollectionFactory,
)


class SQSMetaSubscriber(BaseSubscriber):
    def get_queue_name(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("METASYNC", {}).get("QUEUE_NAME", "")

    def get_queue_config(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("METASYNC", {})

    @property
    def event_handler(self):
        return StatsCollectionFactory
