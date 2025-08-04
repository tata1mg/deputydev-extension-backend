from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, validator
from typing_extensions import Annotated, Literal


class ActorType(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class MessageType(str, Enum):
    TEXT = "TEXT"
    TOOL_USE = "TOOL_USE"
    INFO = "INFO"


class TextMessageData(BaseModel):
    message_type: Literal["TEXT"] = "TEXT"
    text: str
    attachments: Optional[Dict[str, Any]] = None


class ToolUseMessageData(BaseModel):
    message_type: Literal["TOOL_USE"] = "TOOL_USE"
    tool_use_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    tool_response: Optional[Dict[str, Any]] = None


class InfoMessageData(BaseModel):
    message_type: Literal["INFO"] = "INFO"
    info: Dict[str, Any]


MessageData = Annotated[
    Union[TextMessageData, ToolUseMessageData, InfoMessageData], Field(discriminator="message_type")
]


class AgentChatData(BaseModel):
    session_id: int
    actor: ActorType
    message_type: MessageType
    message_data: MessageData
    metadata: Dict[str, Any]

    @validator("message_data")
    def validate_message_data_consistency(self, v: MessageData, values: Dict[str, Any]) -> MessageData:
        if "message_type" in values and v.message_type != values["message_type"].value:
            raise ValueError("message_data.message_type must match message_type field")
        return v


class AgentChatDTO(AgentChatData):
    id: int
    created_at: datetime
    updated_at: datetime


class AgentChatCreateRequest(AgentChatData):
    pass


class AgentChatUpdateRequest(BaseModel):
    actor: Optional[ActorType] = None
    message_type: Optional[MessageType] = None
    message_data: Optional[MessageData] = None
    metadata: Optional[Dict[str, Any]] = None
