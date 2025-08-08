from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated, Literal


class ActorType(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class MessageType(str, Enum):
    TEXT = "TEXT"
    TOOL_USE = "TOOL_USE"
    INFO = "INFO"


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
    tool_response: Optional[Dict[str, Any]] = None
    tool_status: ToolStatus = ToolStatus.PENDING


class ThinkingInfoData(BaseModel):
    message_type: Literal["THINKING"] = "THINKING"
    thinking_summary: str


class InfoMessageData(BaseModel):
    message_type: Literal["INFO"] = "INFO"
    info: str


class TaskCompletionStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ABORTED = "ABORTED"


class TaskCompletionData(BaseModel):
    status: TaskCompletionStatus
    time_taken_seconds: Optional[float] = None


class CodeBlockData(BaseModel):
    message_type: Literal["CODE_BLOCK"] = "CODE_BLOCK"
    code: str
    language: str
    diff: Optional[str] = None
    file_path: Optional[str] = None


MessageData = Annotated[
    Union[TextMessageData, ToolUseMessageData, InfoMessageData, ThinkingInfoData, TaskCompletionData, CodeBlockData],
    Field(discriminator="message_type"),
]

# ACTOR to data mapping. # noqa: ERA001
# USER = TextMessageData  # noqa: ERA001
# ASSISTANT = Union[ToolUseMessageData, ThinkingInfoData, TaskCompletionData, CodeBlockData]. # noqa: ERA001
# SYSTEM = InfoMessageData  # noqa: ERA001


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
