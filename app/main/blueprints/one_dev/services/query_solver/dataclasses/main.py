from enum import Enum
from typing import Any, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


class ToolUseResponseInput(BaseModel):
    tool_name: str
    tool_use_id: str
    response: Dict[str, Any]


class FocusItemTypes(Enum):
    FUNCTION = "function"
    CLASS = "class"
    FILE = "file"
    DIRECTORY = "directory"


class DetailedFocusItem(BaseModel):
    type: FocusItemTypes
    value: str
    chunks: List[ChunkInfo] = []
    path: str


class QuerySolverInput(BaseModel):
    query: Optional[str] = None
    focus_items: List[DetailedFocusItem] = []
    write_mode: bool = False
    session_id: int
    tool_use_response: Optional[ToolUseResponseInput] = None
    previous_query_ids: List[int] = []


class CodeSelectionInput(BaseModel):
    selected_text: str
    file_path: str


class InlineEditInput(BaseModel):
    session_id: int
    query: str
    relevant_chunks: List[Any]
    code_selection: CodeSelectionInput
    auth_data: AuthData


class ResponseMetadataContent(BaseModel):
    query_id: int
    session_id: int


class ResponseMetadataBlock(BaseModel):
    content: ResponseMetadataContent
    type: str
