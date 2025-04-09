from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from app.main.blueprints.deputy_dev.models.dto.message_queue.azure_bus_service_message import (
        AzureBusServiceMessage,
    )
    from app.main.blueprints.deputy_dev.models.dto.message_queue.sqs_message import (
        SQSMessage,
    )


class Response(BaseModel):
    messages: Optional[List[Union["SQSMessage", "AzureBusServiceMessage"]]] = []
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Attribute(BaseModel):
    name: str
    value: str
