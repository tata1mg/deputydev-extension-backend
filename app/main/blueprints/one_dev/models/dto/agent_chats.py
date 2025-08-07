from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
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
    query_id: str
    actor: ActorType
    message_type: MessageType
    message_data: MessageData
    metadata: Dict[str, Any]
    previous_queries: List[str]


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
    previous_queries: Optional[List[int]] = None
