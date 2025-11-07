from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from deputydev_core.llm_handler.dataclasses.main import JSONSchema
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.utils.config_manager import ConfigManager
from pydantic import BaseModel, Field, field_validator

from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import Attachment
from app.backend_common.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.constants.tools import ToolStatus

MAX_DEPUTY_DEV_RULES_LENGTH = ConfigManager.configs["MAX_DEPUTY_DEV_RULES_LENGTH"]


class ToolUseResponseInput(BaseModel):
    tool_name: str
    tool_use_id: str
    response: Dict[str, Any]
    status: ToolStatus = ToolStatus.COMPLETED


class FocusItemTypes(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    FILE = "file"
    DIRECTORY = "directory"
    CODE_SNIPPET = "code_snippet"
    URL = "url"


class ClassFocusItem(BaseModel):
    type: Literal[FocusItemTypes.CLASS] = FocusItemTypes.CLASS
    value: Optional[str] = None
    chunks: List[ChunkInfo] = []
    path: str


class FunctionFocusItem(BaseModel):
    type: Literal[FocusItemTypes.FUNCTION] = FocusItemTypes.FUNCTION
    value: Optional[str] = None
    chunks: List[ChunkInfo] = []
    path: str


class FileFocusItem(BaseModel):
    type: Literal[FocusItemTypes.FILE] = FocusItemTypes.FILE
    value: Optional[str] = None
    chunks: List[ChunkInfo] = []
    path: str


class DirectoryEntry(BaseModel):
    name: str
    type: str


class DirectoryFocusItem(BaseModel):
    type: Literal[FocusItemTypes.DIRECTORY] = FocusItemTypes.DIRECTORY
    value: Optional[str] = None
    path: str
    structure: Optional[List[DirectoryEntry]] = None


class CodeSnippetFocusItem(BaseModel):
    type: Literal[FocusItemTypes.CODE_SNIPPET] = FocusItemTypes.CODE_SNIPPET
    value: Optional[str] = None
    chunks: List[ChunkInfo] = []
    path: str


class UrlFocusItem(BaseModel):
    type: Literal[FocusItemTypes.URL] = FocusItemTypes.URL
    value: Optional[str] = None
    url: str


FocusItem = Annotated[
    Union[ClassFocusItem, FunctionFocusItem, FileFocusItem, DirectoryFocusItem, CodeSnippetFocusItem, UrlFocusItem],
    Field(discriminator="type"),
]


class LLMModel(Enum):
    CLAUDE_3_POINT_5_SONNET = "CLAUDE_3_POINT_5_SONNET"
    CLAUDE_3_POINT_7_SONNET = "CLAUDE_3_POINT_7_SONNET"
    GEMINI_2_POINT_5_PRO = "GEMINI_2_POINT_5_PRO"
    GEMINI_2_POINT_5_FLASH = "GEMINI_2_POINT_5_FLASH"
    GEMINI_2_POINT_5_FLASH_LITE = "GEMINI_2_POINT_5_FLASH_LITE"
    GPT_4_POINT_1 = "GPT_4_POINT_1"
    CLAUDE_4_SONNET = "CLAUDE_4_SONNET"
    CLAUDE_4_SONNET_THINKING = "CLAUDE_4_SONNET_THINKING"
    CLAUDE_4_POINT_5_SONNET = "CLAUDE_4_POINT_5_SONNET"
    QWEN_3_CODER = "QWEN_3_CODER"
    KIMI_K2 = "KIMI_K2"
    OPENROUTER_GPT_5 = "OPENROUTER_GPT_5"
    OPENROUTER_GPT_5_MINI = "OPENROUTER_GPT_5_MINI"
    OPENROUTER_GPT_5_NANO = "OPENROUTER_GPT_5_NANO"
    OPENROUTER_GPT_5_CODEX = "OPENROUTER_GPT_5_CODEX"
    OPENROUTER_GPT_4_POINT_1 = "OPENROUTER_GPT_4_POINT_1"
    OPENROUTER_GROK_4_FAST = "OPENROUTER_GROK_4_FAST"
    OPENROUTER_GROK_CODE_FAST_1 = "OPENROUTER_GROK_CODE_FAST_1"


class Reasoning(Enum):
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RetryReasons(Enum):
    TOOL_USE_FAILED = "TOOL_USE_FAILED"
    THROTTLED = "THROTTLED"
    TOKEN_LIMIT_EXCEEDED = "TOKEN_LIMIT_EXCEEDED"


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


class Repository(BaseModel):
    repo_path: str
    repo_name: str
    root_directory_context: str
    is_working_repository: bool


class QuerySolverInput(BaseModel):
    query: Optional[str] = None
    write_mode: bool = False
    session_id: int
    batch_tool_responses: Optional[List[ToolUseResponseInput]] = None
    deputy_dev_rules: Optional[str] = None
    user_team_id: int
    session_type: str
    os_name: Optional[str] = None
    shell: Optional[str] = None
    vscode_env: Optional[str] = None
    repositories: Optional[List[Repository]] = None
    search_web: Optional[bool] = False
    is_lsp_ready: Optional[bool] = False
    is_indexing_ready: Optional[bool] = False
    is_embeddings_ready: Optional[bool] = False
    is_embedding_done: Optional[bool] = False  # deprecated, use is_embeddings_ready
    llm_model: Optional[LLMModel] = None
    reasoning: Optional[str] = None
    client_tools: List[ClientTool] = []
    retry_reason: Optional[RetryReasons] = None
    attachments: List[Attachment] = []
    focus_items: List[FocusItem] = []

    @field_validator("deputy_dev_rules")
    def character_limit(cls, v: Optional[str]) -> Optional[str]:  # noqa: N805
        if v is None:
            return None
        if len(v) > MAX_DEPUTY_DEV_RULES_LENGTH:
            return None
        return v


class QuerySolverResumeInput(BaseModel):
    session_id: int
    user_team_id: int
    session_type: str
    resume_query_id: str
    resume_offset_id: Optional[str] = None


class LineRange(BaseModel):
    start_line: int
    end_line: int


class CodeSelectionInput(BaseModel):
    selected_text: str
    file_path: str
    line_range: Optional[LineRange] = None


class InlineEditInput(BaseModel):
    session_id: int
    query: Optional[str] = None
    tool_use_response: Optional[ToolUseResponseInput] = None
    tool_choice: Literal["none", "auto", "required"] = "auto"
    code_selection: Optional[CodeSelectionInput] = None
    is_lsp_ready: bool = False
    repo_path: Optional[str] = None
    auth_data: AuthData
    deputy_dev_rules: Optional[str] = None
    relevant_chunks: List[Any] = []
    llm_model: Optional[LLMModel] = LLMModel.CLAUDE_3_POINT_7_SONNET

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
    query_id: str
    session_id: int


class ResponseMetadataBlock(BaseModel):
    content: ResponseMetadataContent
    type: str


class SessionSummaryBlock(BaseModel):
    type: str = "SESSION_SUMMARY"
    content: Dict[str, int | str]


class TaskCompletionContent(BaseModel):
    query_id: int
    success: bool = True
    summary: Optional[str] = None


class TaskCompletionBlock(BaseModel):
    content: TaskCompletionContent
    type: str


class UserQueryEnhancerInput(BaseModel):
    session_id: int
    user_query: str


class StreamErrorData(BaseModel):
    type: str
    message: Optional[Any] = None
    status: str
