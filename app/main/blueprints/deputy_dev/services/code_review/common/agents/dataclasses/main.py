from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels


class AgentTypes(Enum):
    SECURITY = "security"
    CODE_COMMUNICATION = "code_communication"
    PERFORMANCE_OPTIMIZATION = "performance_optimisation"
    CODE_MAINTAINABILITY = "code_maintainability"
    ERROR = "error"
    BUSINESS_LOGIC_VALIDATION = "business_logic_validation"
    PR_SUMMARY = "pr_summary"
    COMMENT_VALIDATION = "comment_validation"
    COMMENT_SUMMARIZATION = "comment_summarization"
    CUSTOM_COMMENTER_AGENT = "custom_commenter_agent"


class AgentAndInitParams(BaseModel):
    agent_type: AgentTypes
    init_params: Dict[str, Any] = {}


class AgentRunResult(BaseModel):
    prompt_tokens_exceeded: bool
    agent_result: Optional[Union[Dict[str, Any], str]] = None  # String in case of PR summary
    agent_name: str
    agent_type: AgentTypes
    model: LLModels
    tokens_data: Optional[Dict[str, Dict[str, Any]]] = None
    display_name: Optional[str] = None
