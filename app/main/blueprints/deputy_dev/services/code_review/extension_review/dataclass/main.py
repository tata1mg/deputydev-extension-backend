from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class RequestType(str, Enum):
    """Request types for multi-agent review API."""
    QUERY = "query"
    TOOL_USE_RESPONSE = "tool_use_response"
    TOOL_USE_FAILED = "tool_use_failed"


class ToolUseResponseData(BaseModel):
    """Tool use response data structure."""
    tool_name: str
    tool_use_id: str
    response: Any


class AgentRequestItem(BaseModel):
    """Individual agent request item in the multi-agent payload."""
    agent_id: int
    review_id: int
    type: RequestType
    tool_use_response: Optional[ToolUseResponseData] = None


class MultiAgentReviewRequest(BaseModel):
    """Multi-agent review request payload."""
    agents: List[AgentRequestItem]
    review_id: int
    connection_id: str
    user_team_id: Optional[int] = None



class AgentTaskResult(BaseModel):
    """Result from individual agent task execution."""
    agent_id: int
    agent_name: str
    agent_type: str
    status: str  # "success", "error", "tool_use_request"
    result: Dict[str, Any]
    tokens_data: Dict[str, Any] = {}
    model: str = ""
    display_name: str = ""
    error_message: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message structure for agent responses."""
    type: str  # "AGENT_RESULT", "STREAM_ERROR", "STREAM_START", "STREAM_END"
    agent_id: Optional[int] = None
    data: Dict[str, Any] = {}
    timestamp: Optional[str] = None
