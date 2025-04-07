from torpedo import CONFIG
from app.backend_common.utils.types import CloudProviders
from app.main.blueprints.deputy_dev.services.message_queue.genai.sqs_genai_subscriber import SQSGenaiSubscriber
from app.main.blueprints.deputy_dev.services.message_queue.genai.azure_bus_service_genai_subscriber import (
    AzureBusServiceGenAiSubscriber,
)
from typing import Union
from app.main.blueprints.deputy_dev.services.message_queue.models.sqs_model import SQSMessage
from app.main.blueprints.deputy_dev.services.message_queue.models.azure_bus_service_model import AzureBusServiceMessage

config = CONFIG.config


class MessageQueueFactory:
    cloud_provider = config.get("CLOUD_PROVIDER")
    genai_subscribers = {
        CloudProviders.AZURE.value: AzureBusServiceGenAiSubscriber,
        CloudProviders.AWS.value: SQSGenaiSubscriber,
    }
    meta_subscribers = {}
    message_models = {
        CloudProviders.AZURE.value: AzureBusServiceMessage,
        CloudProviders.AWS.value: SQSMessage,
    }

    @classmethod
    def genai_subscriber(cls) -> [Union[AzureBusServiceGenAiSubscriber, SQSGenaiSubscriber]]:
        return cls.genai_subscribers[cls.cloud_provider]

    @classmethod
    def message_model(cls):
        return cls.message_models[cls.cloud_provider]
