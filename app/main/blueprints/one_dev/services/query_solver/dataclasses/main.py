from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ToolUseResponseInput(BaseModel):
    tool_name: str
    tool_use_id: str
    response: Dict[str, Any]


class QuerySolverInput(BaseModel):
    query: Optional[str] = None
    relevant_chunks: List[str] = []
    write_mode: bool = False
    session_id: int
    tool_use_response: Optional[ToolUseResponseInput] = None
