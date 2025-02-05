from app.common.services.chunking.strategies.base_chunker import BaseChunker
from app.common.services.chunking.strategies.legacy_chunker import LegacyChunker
from app.common.services.chunking.strategies.metadata_chunking.base_metadata_chunker import (
    BaseMetadataChunker,
)


class ChunkingStrategyFactory:
    # We can keep a map of extension is to specific meta data chunking class that overrides base meta_data chunking methods
    _language_specific_chunkers = {}

    @classmethod
    def create_strategy(cls, path: str, is_eligible_for_new_chunking: bool) -> BaseChunker:
        """Creates appropriate chunking strategy"""
        if not is_eligible_for_new_chunking:
            return LegacyChunker

        ext = path.split(".")[-1].lower()
        # return BaseMetadataChunker
        return cls._language_specific_chunkers.get(ext, BaseMetadataChunker)
