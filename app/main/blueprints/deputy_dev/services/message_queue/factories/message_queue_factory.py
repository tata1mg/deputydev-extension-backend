from typing import Union

from app.backend_common.utils.sanic_wrapper import CONFIG
from app.backend_common.utils.types.types import CloudProviders
from app.main.blueprints.deputy_dev.services.message_queue.subscribers.genai.azure_bus_service_genai_subscriber import (
    AzureBusServiceGenAiSubscriber,
)
from app.main.blueprints.deputy_dev.services.message_queue.subscribers.genai.sqs_genai_subscriber import (
    SQSGenaiSubscriber,
)
from app.main.blueprints.deputy_dev.services.message_queue.subscribers.meta_sync.azure_bus_service_meta_subscriber import (
    AzureBusServiceMetaSubscriber,
)
from app.main.blueprints.deputy_dev.services.message_queue.subscribers.meta_sync.sqs_meta_subscriber import (
    SQSMetaSubscriber,
)

config = CONFIG.config


class MessageQueueFactory:
    cloud_provider = config.get("CLOUD_PROVIDER")
    genai_subscribers = {
        CloudProviders.AZURE.value: AzureBusServiceGenAiSubscriber,
        CloudProviders.AWS.value: SQSGenaiSubscriber,
    }
    meta_subscribers = {
        CloudProviders.AZURE.value: AzureBusServiceMetaSubscriber,
        CloudProviders.AWS.value: SQSMetaSubscriber,
    }

    @classmethod
    def genai_subscriber(cls) -> [Union[AzureBusServiceGenAiSubscriber, SQSGenaiSubscriber]]:
        return cls.genai_subscribers[cls.cloud_provider]

    @classmethod
    def meta_subscriber(cls) -> [Union[AzureBusServiceMetaSubscriber, SQSMetaSubscriber]]:
        return cls.meta_subscribers[cls.cloud_provider]
