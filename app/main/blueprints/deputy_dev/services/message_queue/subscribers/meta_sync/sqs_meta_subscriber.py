from app.main.blueprints.deputy_dev.services.message_queue.subscribers.base.sqs_subscriber import (
    SQSSubscriber,
)
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_factory import (
    StatsCollectionFactory,
)
from sanic.log import logger

class SQSMetaSubscriber(SQSSubscriber):
    def get_queue_name(self):
        logger.info(f"METASYNC queue getting picked: {self.config.get('SQS')}")
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("METASYNC", {}).get("QUEUE_NAME", "")

    def get_queue_config(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("METASYNC", {})

    @property
    def event_handler(self):
        return StatsCollectionFactory
