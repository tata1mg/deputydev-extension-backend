from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.utils.config_manager import ConfigManager
from pydantic import BaseModel, field_validator

from app.backend_common.services.llm.dataclasses.main import JSONSchema
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


class DirectoryEntry(BaseModel):
    name: str
    type: str


class DetailedDirectoryItem(BaseModel):
    path: str
    value: Optional[str] = None
    structure: Optional[List[DirectoryEntry]] = None


class Url(BaseModel):
    value: str
    url: str
    type: str
    keyword: str


class LLMModel(Enum):
    CLAUDE_3_POINT_5_SONNET = "CLAUDE_3_POINT_5_SONNET"
    GEMINI_2_POINT_5_PRO = "GEMINI_2_POINT_5_PRO"
    GEMINI_2_POINT_5_FLASH = "GEMINI_2_POINT_5_FLASH"
    GPT_4_POINT_1 = "GPT_4_POINT_1"
    CLAUDE_4_SONNET = "CLAUDE_4_SONNET"
    CLAUDE_4_SONNET_THINKING = "CLAUDE_4_SONNET_THINKING"


class ToolMetadataTypes(Enum):
    MCP = "MCP"


class MCPToolMetadata(BaseModel):
    type: ToolMetadataTypes = ToolMetadataTypes.MCP
    server_id: str
    tool_name: str


class ClientTool(BaseModel):
    name: str
    description: str
    input_schema: JSONSchema
    tool_metadata: MCPToolMetadata


class Attachment(BaseModel):
    attachment_id: int


class Repository(BaseModel):
    repo_path: str
    repo_name: str
    root_directory_context: str
    is_working_repository: bool


class QuerySolverInput(BaseModel):
    query: Optional[str] = None
    focus_items: List[DetailedFocusItem] = []
    directory_items: Optional[List[DetailedDirectoryItem]] = None
    write_mode: bool = False
    session_id: int
    tool_use_failed: Optional[bool] = None
    batch_tool_responses: Optional[List[ToolUseResponseInput]] = None
    tool_use_response: Optional[ToolUseResponseInput] = None
    previous_query_ids: List[int] = []
    deputy_dev_rules: Optional[str] = None
    user_team_id: int
    session_type: str
    urls: List[Url] = []
    os_name: Optional[str] = None
    shell: Optional[str] = None
    vscode_env: Optional[str] = None
    repositories: Optional[List[Repository]] = None
    search_web: Optional[bool] = False
    llm_model: Optional[LLMModel] = None
    client_tools: List[ClientTool] = []
    attachments: List[Attachment] = []
    is_embedding_done: Optional[bool] = True

    @field_validator("deputy_dev_rules")
    def character_limit(cls, v: Optional[str]) -> Optional[str]:  # noqa: N805
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
    def character_limit(cls, v: Optional[str]) -> Optional[str]:  # noqa: N805
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


class StreamErrorData(BaseModel):
    type: str
    message: Optional[Any] = None
    status: str
