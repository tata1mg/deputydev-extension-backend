from typing import Type, Union

from torpedo import CONFIG

from app.backend_common.utils.types import CloudProviders
from app.backend_common.wrappers.message_queue.managers.azure_bus_service_manager import (
    AzureServiceBusManager,
)
from app.backend_common.wrappers.message_queue.managers.sqs_manager import SQSManager


class MessageQueueManagerFactory:
    message_queue_managers = {CloudProviders.AZURE.value: AzureServiceBusManager, CloudProviders.AWS.value: SQSManager}

    @classmethod
    def manager(cls) -> Type[Union[AzureServiceBusManager, SQSManager]]:
        cloud_provider = CONFIG.config["CLOUD_PROVIDER"]
        return cls.message_queue_managers[cloud_provider]
