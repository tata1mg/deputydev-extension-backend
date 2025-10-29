from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated, Literal

from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import Attachment
from app.main.blueprints.one_dev.constants.tools import ToolStatus
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    FocusItem,
    Repository,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    PlanSteps,
)


class ActorType(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class MessageType(str, Enum):
    TEXT = "TEXT"
    TOOL_USE = "TOOL_USE"
    INFO = "INFO"
    TASK_COMPLETION = "TASK_COMPLETION"
    THINKING = "THINKING"
    CODE_BLOCK = "CODE_BLOCK"
    TASK_PLAN = "TASK_PLAN"


class TextMessageData(BaseModel):
    message_type: Literal["TEXT"] = "TEXT"
    text: str
    attachments: List[Attachment] = []
    focus_items: List[FocusItem] = []
    vscode_env: Optional[str] = None
    repositories: Optional[List[Repository]] = None


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
    ignore_in_chat: Optional[bool] = False


class InfoMessageData(BaseModel):
    message_type: Literal["INFO"] = "INFO"
    info: str


class TaskCompletionStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ABORTED = "ABORTED"


class TaskCompletionData(BaseModel):
    message_type: Literal["TASK_COMPLETION"] = "TASK_COMPLETION"
    status: TaskCompletionStatus
    time_taken_seconds: Optional[float] = None


class CodeBlockData(BaseModel):
    message_type: Literal["CODE_BLOCK"] = "CODE_BLOCK"
    code: str
    language: str
    diff: Optional[str] = None
    file_path: Optional[str] = None


class TaskPlanData(BaseModel):
    message_type: Literal["TASK_PLAN"] = "TASK_PLAN"
    latest_plan_steps: List[PlanSteps] = []


MessageData = Annotated[
    Union[
        TextMessageData,
        ToolUseMessageData,
        InfoMessageData,
        ThinkingInfoData,
        TaskCompletionData,
        CodeBlockData,
        TaskPlanData,
    ],
    Field(discriminator="message_type"),
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
    previous_queries: Optional[List[str]] = None
