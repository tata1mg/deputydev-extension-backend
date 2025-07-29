from typing import Optional

from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    BaseCodeGenFeaturePayload,
)
from deputydev_core.services.chunking.chunk_info import ChunkInfo


class CodePlanGenerationInput(BaseCodeGenFeaturePayload):
    query: str
    is_llm_reranking_enabled: Optional[bool] = False
    relevant_chunks: list[ChunkInfo]
    focus_chunks: Optional[list[ChunkInfo]]
