from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel


class TextSnippet(BaseModel):
    start_line: int
    end_line: int
    file_path: str


class TextSelectionQuery(BaseModel):
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    custom_instructions: Optional[str] = None


class PlainTextQuery(BaseModel):
    text: str
    focus_files: List[str] = []
    focus_snippets: List[TextSnippet] = []


class FeatureNextAction(Enum):
    CONTINUE_CHAT = "CONTINUE_CHAT"
    HOME_SCREEN = "HOME_SCREEN"
    ERROR_OUT_AND_END = "ERROR_OUT_AND_END"


class FeatureHandlingRedirections(BaseModel):
    success_redirect: FeatureNextAction
    error_redirect: FeatureNextAction


class FeatureHandlingResult(BaseModel):
    job_id: int
    session_id: str
    redirections: FeatureHandlingRedirections


class PRConfig(BaseModel):
    source_branch: Optional[str] = None
    destination_branch: str
    pr_title_prefix: Optional[str] = None
    commit_message_prefix: Optional[str] = None


class FinalSuccessJob(BaseModel):
    job_id: int
    session_id: str
    display_response: Optional[str] = None
    diff: Optional[Dict[str, List[Tuple[int, int, str]]]] = None
    create_pr: Optional[bool] = None
    pr_link: Optional[str] = None
    existing_pr: Optional[bool] = None
    next_action: FeatureNextAction = FeatureNextAction.HOME_SCREEN


class FinalFailedJob(BaseModel):
    job_id: Optional[int] = None
    display_message: str
    next_action: FeatureNextAction = FeatureNextAction.ERROR_OUT_AND_END


class RegisteredRepo(BaseModel):
    workspace_id: int
    repo_name: str
    repo_url: str


class LocalUserDetails(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
