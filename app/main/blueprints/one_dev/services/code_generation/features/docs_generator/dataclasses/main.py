from typing import Optional

from app.main.blueprints.one_dev.services.code_generation.dataclasses.main import (
    PRConfig,
)
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    BaseCodeGenFeaturePayload,
)
from deputydev_core.services.chunking.chunk_info import ChunkInfo


class CodeDocsGenerationInput(BaseCodeGenFeaturePayload):
    query: str
    custom_instructions: Optional[str] = None
    create_pr: Optional[bool] = None
    pr_config: Optional[PRConfig] = None
    apply_diff: Optional[bool] = None
    relevant_chunks: list[ChunkInfo]
    focus_chunks: Optional[list[ChunkInfo]]
    is_llm_reranking_enabled: Optional[bool] = False
