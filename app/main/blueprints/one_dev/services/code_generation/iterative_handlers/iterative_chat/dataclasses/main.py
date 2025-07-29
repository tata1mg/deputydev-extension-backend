from typing import Dict, List, Union

from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.dataclass.main import (
    BaseCodeGenIterativeHandlerPayload,
)
from deputydev_core.services.chunking.chunk_info import ChunkInfo


class IterativeChatInput(BaseCodeGenIterativeHandlerPayload):
    query: str
    relevant_chunks: List[ChunkInfo]
    is_llm_reranking_enabled: bool
    relevant_chat_history: List[Dict[str, Union[str, int]]]
