from typing import Union

from torpedo import CONFIG

from app.backend_common.utils.types import CloudProviders
from app.main.blueprints.deputy_dev.services.message_queue.genai.azure_bus_service_genai_subscriber import (
    AzureBusServiceGenAiSubscriber,
)
from app.main.blueprints.deputy_dev.services.message_queue.genai.sqs_genai_subscriber import (
    SQSGenaiSubscriber,
)
from app.main.blueprints.deputy_dev.services.message_queue.meta_sync.azure_bus_service_meta_subscriber import (
    AzureBusServiceMetaSubscriber,
)
from app.main.blueprints.deputy_dev.services.message_queue.meta_sync.sqs_meta_subscriber import (
    SQSMetaSubscriber,
)
from app.main.blueprints.deputy_dev.models.dto.message_queue.azure_bus_service_model import (
    AzureBusServiceMessage,
)
from app.main.blueprints.deputy_dev.models.dto.message_queue.sqs_model import (
    SQSMessage,
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
    message_models = {
        CloudProviders.AZURE.value: AzureBusServiceMessage,
        CloudProviders.AWS.value: SQSMessage,
    }
    queue_config_key = {
        CloudProviders.AZURE.value: "AZURE_BUS_SERVICE",
        CloudProviders.AWS.value: "SQS",
    }

    @classmethod
    def genai_subscriber(cls) -> [Union[AzureBusServiceGenAiSubscriber, SQSGenaiSubscriber]]:
        return cls.genai_subscribers[cls.cloud_provider]

    @classmethod
    def meta_subscriber(cls) -> [Union[AzureBusServiceMetaSubscriber, SQSMetaSubscriber]]:
        return cls.meta_subscribers[cls.cloud_provider]

    @classmethod
    def message_model(cls):
        return cls.message_models[cls.cloud_provider]

    @classmethod
    def is_queue_enabled(cls, config, queue_type):
        key = cls.queue_config_key[cls.cloud_provider]
        config.get(key, {}).get("SUBSCRIBE", {}).get(queue_type, {}).get("ENABLED", False)
        return config
