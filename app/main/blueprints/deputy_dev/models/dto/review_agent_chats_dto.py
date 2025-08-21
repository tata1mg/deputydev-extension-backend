from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated, Literal


class ActorType(str, Enum):
    REVIEW_AGENT = "REVIEW_AGENT"
    ASSISTANT = "ASSISTANT"


class MessageType(str, Enum):
    TEXT = "TEXT"
    TOOL_USE = "TOOL_USE"


class TextMessageData(BaseModel):
    message_type: Literal["TEXT"] = "TEXT"
    text: str
    attachments: Optional[Dict[str, Any]] = None


class ToolStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class ToolUseMessageData(BaseModel):
    message_type: Literal["TOOL_USE"] = "TOOL_USE"
    tool_use_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    tool_response: Optional[Dict[str, Any] | str] = None
    tool_status: ToolStatus = ToolStatus.PENDING


MessageData = Annotated[
    Union[TextMessageData, ToolUseMessageData],
    Field(discriminator="message_type"),
]


class ReviewAgentChatData(BaseModel):
    session_id: int
    agent_id: int
    actor: ActorType
    message_type: MessageType
    message_data: MessageData
    metadata: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ReviewAgentChatDTO(ReviewAgentChatData):
    id: int
    created_at: datetime
    updated_at: datetime


class ReviewAgentChatCreateRequest(ReviewAgentChatData):
    pass


class ReviewAgentChatUpdateRequest(BaseModel):
    actor: Optional[ActorType] = None
    message_type: Optional[MessageType] = None
    message_data: Optional[MessageData] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
