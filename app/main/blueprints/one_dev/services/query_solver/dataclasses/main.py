from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.common.services.chunking.chunk_info import ChunkInfo
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


class ToolUseResponseInput(BaseModel):
    tool_name: str
    tool_use_id: str
    response: Dict[str, Any]


class QuerySolverInput(BaseModel):
    query: Optional[str] = None
    relevant_chunks: List[Any] = []
    write_mode: bool = False
    session_id: int
    tool_use_response: Optional[ToolUseResponseInput] = None


class InlineEditInput(BaseModel):
    session_id: int
    query: str
    relevant_chunks: List[Any]
    code_selection: str
    auth_data: AuthData
