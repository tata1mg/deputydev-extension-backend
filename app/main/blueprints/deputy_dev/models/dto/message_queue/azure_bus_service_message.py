from typing import Optional

from azure.servicebus import ServiceBusReceivedMessage
from pydantic import ConfigDict

from app.main.blueprints.deputy_dev.models.dto.message_queue.base_queue_message import (
    BaseQueueMessage,
)


class AzureBusServiceMessage(BaseQueueMessage):
    received_message: Optional[ServiceBusReceivedMessage] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
