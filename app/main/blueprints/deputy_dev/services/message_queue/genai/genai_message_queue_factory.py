from torpedo import CONFIG
from app.backend_common.utils.types import CloudProviders
from app.main.blueprints.deputy_dev.services.message_queue.genai.sqs_genai_subscriber import SQSGenaiSubscriber
from app.main.blueprints.deputy_dev.services.message_queue.genai.azure_bus_service_genai_subscriber import (
    AzureBusServiceGenAiSubscriber,
)
from typing import Union
from app.main.blueprints.deputy_dev.services.message_queue.sqs_model import SQSMessage

config = CONFIG.config


# TODO: Remove this
class GenAiMessageQueueFactory:
    cloud_provider = config.get("CLOUD_PROVIDER")

    subscribers = {
        CloudProviders.AZURE.value: AzureBusServiceGenAiSubscriber,
        CloudProviders.AWS.value: SQSGenaiSubscriber,
    }

    message_models = {
        CloudProviders.AZURE.value: AzureBusServiceGenAiSubscriber,
        CloudProviders.AWS.value: SQSMessage,
    }

    @classmethod
    def subscriber(cls) -> [Union[AzureBusServiceGenAiSubscriber, SQSGenaiSubscriber]]:
        return cls.subscribers[cls.cloud_provider]

    @classmethod
    def message_model(cls):
        return cls.message_models[cls.cloud_provider]
