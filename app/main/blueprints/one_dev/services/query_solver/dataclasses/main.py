from enum import Enum
from typing import Any, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.utils.config_manager import ConfigManager
from pydantic import BaseModel, field_validator

from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData

MAX_DEPUTY_DEV_RULES_LENGTH = ConfigManager.configs["MAX_DEPUTY_DEV_RULES_LENGTH"]


class ToolUseResponseInput(BaseModel):
    tool_name: str
    tool_use_id: str
    response: Dict[str, Any]


class FocusItemTypes(Enum):
    FUNCTION = "function"
    CLASS = "class"
    FILE = "file"
    DIRECTORY = "directory"
    CODE_SNIPPET = "code_snippet"
    URL = "url"


class DetailedFocusItem(BaseModel):
    type: FocusItemTypes
    value: Optional[str] = None
    chunks: List[ChunkInfo] = []
    path: Optional[str] = ""
    url: Optional[str] = ""


class Url(BaseModel):
    value: str
    url: str
    type: str
    keyword: str


class QuerySolverInput(BaseModel):
    query: Optional[str] = None
    focus_items: List[DetailedFocusItem] = []
    write_mode: bool = False
    session_id: int
    tool_use_failed: Optional[bool] = None
    tool_use_response: Optional[ToolUseResponseInput] = None
    previous_query_ids: List[int] = []
    deputy_dev_rules: Optional[str] = None
    user_team_id: Optional[int] = None
    session_type: Optional[str] = None
    urls: Optional[List[Url]] = []

    @field_validator("deputy_dev_rules")
    def character_limit(cls, v: Optional[str]):
        if v is None:
            return None
        if len(v) > MAX_DEPUTY_DEV_RULES_LENGTH:
            return None
        return v


class CodeSelectionInput(BaseModel):
    selected_text: str
    file_path: str


class InlineEditInput(BaseModel):
    session_id: int
    query: Optional[str] = None
    tool_use_response: Optional[ToolUseResponseInput] = None
    code_selection: Optional[CodeSelectionInput] = None
    auth_data: AuthData
    deputy_dev_rules: Optional[str] = None
    relevant_chunks: List[Any] = []

    @field_validator("deputy_dev_rules")
    def character_limit(cls, v: Optional[str]):
        if v is None:
            return None
        if len(v) > MAX_DEPUTY_DEV_RULES_LENGTH:
            return None
        return v


class ResponseMetadataContent(BaseModel):
    query_id: int
    session_id: int


class ResponseMetadataBlock(BaseModel):
    content: ResponseMetadataContent
    type: str
