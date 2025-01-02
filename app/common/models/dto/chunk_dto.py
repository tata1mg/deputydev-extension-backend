from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChunkDTO(BaseModel):
    id: Optional[str] = None
    chunk_hash: str
    text: str
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChunkDTOWithVector(BaseModel):
    vector: List[float]
    dto: ChunkDTO
