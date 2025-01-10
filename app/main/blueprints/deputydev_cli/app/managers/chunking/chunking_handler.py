from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from prompt_toolkit.shortcuts.progress_bar import ProgressBar, ProgressBarCounter

from app.common.services.chunking.chunk_info import ChunkInfo
from app.common.services.chunking.chunker.handlers.vector_db_chunker import (
    VectorDBChunker,
)
from app.common.services.chunking.vector_store.main import ChunkVectorScoreManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.utils.app_logger import AppLogger
from app.main.blueprints.deputydev_cli.app.managers.embedding.embedding_manager import OneDevEmbeddingManager


class OneDevCLIChunker(VectorDBChunker):
    def __init__(
        self,
        local_repo: BaseLocalRepo,
        process_executor: ProcessPoolExecutor,
        weaviate_client: WeaviateSyncAndAsyncClients,
        embedding_manager: OneDevEmbeddingManager,
        usage_hash: str,
        chunkable_files_and_hashes: Dict[str, str],
        progress_bar: Optional[ProgressBar] = None,
        use_new_chunking: bool = True,
    ):
        super().__init__(
            local_repo,
            process_executor,
            weaviate_client,
            embedding_manager,
            usage_hash,
            chunkable_files_and_hashes,
            use_new_chunking,
        )
        self.embedding_manager = embedding_manager
        self.progress_bar = progress_bar
        self.file_progressbar_counter: Optional[ProgressBarCounter[int]] = None

    async def add_chunk_embeddings(self, chunks: List[ChunkInfo], len_checkpoints: Optional[int] = None) -> None:
        texts_to_embed = [
            chunk.get_chunk_content_with_meta_data(add_ellipsis=False, add_lines=False, add_class_function_info=True)
            for chunk in chunks
        ]
        embeddings, _input_tokens = await self.embedding_manager.embed_text_array(texts=texts_to_embed, progress_bar_counter=self.file_progressbar_counter, len_checkpoints=len_checkpoints)
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

    async def handle_chunking_batch(
        self,
        files_to_chunk_batch: List[Tuple[str, str]],
    ) -> List[ChunkInfo]:
        """
        Handles a batch of files to be chunked
        """
        batched_chunks: List[ChunkInfo] = await self.file_chunk_creator.create_chunks_from_files(
            dict(files_to_chunk_batch),
            self.local_repo.repo_path,
            self.use_new_chunking,
            process_executor=self.process_executor,
        )
        if batched_chunks:
            await self.add_chunk_embeddings(batched_chunks, len_checkpoints=len(files_to_chunk_batch))
            await ChunkVectorScoreManager(
                local_repo=self.local_repo, weaviate_client=self.weaviate_client
            ).add_differential_chunks_to_store(batched_chunks, usage_hash=self.usage_hash)
        return batched_chunks

    async def batch_chunk_inserter(
        self,
        batched_files_to_store: List[List[Tuple[str, str]]],
    ) -> List[ChunkInfo]:
        if self.progress_bar:
            total_files = sum(len(batch_files) for batch_files in batched_files_to_store)
            self.file_progressbar_counter = self.progress_bar(
                range(total_files), label="Setting up DeputyDev's intelligence"
            )
            AppLogger.log_debug(f"Processing {len(range(total_files))} batches")

        return await super().batch_chunk_inserter(batched_files_to_store)
