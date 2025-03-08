from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel


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
