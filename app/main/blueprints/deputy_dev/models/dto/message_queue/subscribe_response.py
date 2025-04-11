from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict

from app.main.blueprints.deputy_dev.models.dto.message_queue.azure_bus_service_message import (
    AzureBusServiceMessage,
)
from app.main.blueprints.deputy_dev.models.dto.message_queue.sqs_message import (
    SQSMessage,
)


class SubscribeResponse(BaseModel):
    messages: Optional[List[Union[SQSMessage, AzureBusServiceMessage]]] = []
    model_config = ConfigDict(arbitrary_types_allowed=True)
