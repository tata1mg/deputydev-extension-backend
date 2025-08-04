from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ActorType(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class MessageType(str, Enum):
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    TOOL_RESPONSE = "TOOL_RESPONSE"
    TOOL_REQUEST = "TOOL_REQUEST"


class AgentChatData(BaseModel):
    session_id: int
    actor: ActorType
    message_type: MessageType
    query_id: Optional[int] = None
    query_text: Optional[str] = None
    attachments: Optional[Dict[str, Any]] = None
    selected_code_snippets: Optional[Dict[str, Any]] = None
    tool_name: Optional[str] = None
    tool_use_id: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]


class AgentChatDTO(AgentChatData):
    id: int
    created_at: datetime
    updated_at: datetime


class AgentChatCreateRequest(AgentChatData):
    pass


class AgentChatUpdateRequest(BaseModel):
    actor: Optional[ActorType] = None
    message_type: Optional[MessageType] = None
    query_id: Optional[int] = None
    query_text: Optional[str] = None
    attachments: Optional[Dict[str, Any]] = None
    selected_code_snippets: Optional[Dict[str, Any]] = None
    tool_name: Optional[str] = None
    tool_use_id: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
