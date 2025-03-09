from pydantic import BaseModel
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from typing import Optional


class RerankingInput(BaseModel):
    query: str
    relevant_chunks: list[ChunkInfo]
    focus_chunks: Optional[list[ChunkInfo]]
