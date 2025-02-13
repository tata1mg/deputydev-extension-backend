from typing import List

from pydantic import BaseModel


class QuerySolverInput(BaseModel):
    query: str
    relevant_chunks: List[str] = []
    write_mode: bool = False
