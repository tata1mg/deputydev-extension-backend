from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.main.blueprints.deputy_dev.constants.constants import IdeReviewCommentStatus, ReviewType


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
    """WebSocket message structure specifically for agent execution results."""

    type: str
    agent_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = {}
    timestamp: Optional[str] = None


class FileWiseChanges(BaseModel):
    file_path: str
    file_name: str
    status: str
    line_changes: Dict[str, int]
    diff: str


class ReviewRequest(BaseModel):
    repo_name: str
    origin_url: str
    source_branch: str
    target_branch: str
    source_commit: str
    target_commit: str
    diff_attachment_id: Optional[str] = None
    file_wise_diff: List[FileWiseChanges]
    review_type: ReviewType


class CommentUpdateRequest(BaseModel):
    id: int
    comment_status: IdeReviewCommentStatus


class GetRepoIdRequest(BaseModel):
    repo_name: str
    origin_url: str
