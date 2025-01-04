from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from prompt_toolkit.shortcuts.progress_bar import ProgressBar

from app.common.services.chunking.chunk_info import ChunkInfo
from app.common.services.chunking.chunker.handlers.vector_db_chunker import (
    VectorDBChunker,
)
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients


class OneDevCLIChunker(VectorDBChunker):
    def __init__(
        self,
        local_repo: BaseLocalRepo,
        process_executor: ProcessPoolExecutor,
        weaviate_client: WeaviateSyncAndAsyncClients,
        embedding_manager: BaseEmbeddingManager,
        usage_hash: str,
        chunkable_files_and_hashes: Dict[str, str],
        progress_bar: Optional[ProgressBar] = None,
        use_new_chunking: bool = True,
    ):
        self.progress_bar = progress_bar
        super().__init__(
            local_repo,
            process_executor,
            weaviate_client,
            embedding_manager,
            usage_hash,
            chunkable_files_and_hashes,
            use_new_chunking,
        )

    async def batch_chunk_inserter(
        self,
        batched_files_to_store: List[List[Tuple[str, str]]],
    ) -> List[ChunkInfo]:
        all_chunks: List[ChunkInfo] = []
        iterable_batches = batched_files_to_store
        if self.progress_bar:
            iterable_batches = self.progress_bar(
                batched_files_to_store,
                label="Setting up DeputyDev's intelligence",
                total=len(batched_files_to_store),
                remove_when_done=True,
            )
        for batch_files in iterable_batches:
            chunk_obj = await self.handle_chunking_batch(
                files_to_chunk_batch=batch_files,
            )
            all_chunks.extend(chunk_obj)
        return all_chunks
