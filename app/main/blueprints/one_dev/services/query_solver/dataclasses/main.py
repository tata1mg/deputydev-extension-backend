from enum import Enum
from typing import Any, Dict, List, Literal, Optional

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


class LLMModel(Enum):
    CLAUDE_3_POINT_5_SONNET = "CLAUDE_3_POINT_5_SONNET"
    GEMINI_2_POINT_5_PRO = "GEMINI_2_POINT_5_PRO"
    GPT_4_POINT_1 = "GPT_4_POINT_1"


class ToolMetadataTypes(Enum):
    MCP = "MCP"


class MCPToolMetadata(BaseModel):
    type: Literal[ToolMetadataTypes.MCP]
    server_id: str
    tool_name: str


class ClientTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    tool_metadata: MCPToolMetadata
class Attachment(BaseModel):
    attachment_id: int


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
    os_name: Optional[str] = None
    shell: Optional[str] = None
    vscode_env: Optional[str] = None
    search_web: Optional[bool] = False
    llm_model: Optional[LLMModel] = LLMModel.CLAUDE_3_POINT_5_SONNET
    client_tools: List[ClientTool] = []
    attachments: List[Attachment] = []

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
    tool_choice: Literal["none", "auto", "required"] = "auto"
    code_selection: Optional[CodeSelectionInput] = None
    auth_data: AuthData
    deputy_dev_rules: Optional[str] = None
    relevant_chunks: List[Any] = []
    llm_model: Optional[LLMModel] = LLMModel.CLAUDE_3_POINT_5_SONNET

    @field_validator("deputy_dev_rules")
    def character_limit(cls, v: Optional[str]):
        if v is None:
            return None
        if len(v) > MAX_DEPUTY_DEV_RULES_LENGTH:
            return None
        return v


class TerminalCommandEditInput(BaseModel):
    session_id: int
    query: str
    old_terminal_command: str
    os_name: str
    shell: str
    auth_data: AuthData


class ResponseMetadataContent(BaseModel):
    query_id: int
    session_id: int


class ResponseMetadataBlock(BaseModel):
    content: ResponseMetadataContent
    type: str


class UserQueryEnhancerInput(BaseModel):
    session_id: int
    user_query: str
