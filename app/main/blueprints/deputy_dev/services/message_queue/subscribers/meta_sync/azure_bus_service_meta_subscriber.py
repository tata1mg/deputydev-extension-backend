from app.main.blueprints.deputy_dev.services.message_queue.subscribers.base.azure_bus_service_subscriber import (
    AzureBusServiceSubscriber,
)
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_factory import (
    StatsCollectionFactory,
)


class AzureBusServiceMetaSubscriber(AzureBusServiceSubscriber):
    def get_queue_name(self):
        return self.config.get("AZURE_BUS_SERVICE", {}).get("SUBSCRIBE", {}).get("METASYNC", {}).get("QUEUE_NAME", "")

    def get_queue_config(self):
        return self.config.get("AZURE_BUS_SERVICE", {}).get("SUBSCRIBE", {}).get("METASYNC", {})

    @property
    def event_handler(self):
        return StatsCollectionFactory
