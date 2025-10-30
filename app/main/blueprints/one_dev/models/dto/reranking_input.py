from deputydev_core.services.chunking.chunk_info import ChunkInfo
from pydantic import BaseModel


class RerankingInput(BaseModel):
    query: str
    relevant_chunks: list[ChunkInfo]
