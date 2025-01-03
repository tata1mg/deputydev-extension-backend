from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChunkFileDTO(BaseModel):
    id: Optional[str] = None
    chunk_hash: str
    file_path: str
    file_hash: str
    start_line: int
    end_line: int
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
