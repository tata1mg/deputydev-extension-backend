from abc import ABC, abstractmethod
from typing import List, Union

from app.common.services.chunking.chunk_info import ChunkInfo
from app.common.services.chunking.dataclass.main import NeoSpan


class BaseChunker(ABC):
    @abstractmethod
    def chunk_code(self, tree, content: bytes, max_chars, coalesce, language) -> Union[List[ChunkInfo], List[NeoSpan]]:
        pass
