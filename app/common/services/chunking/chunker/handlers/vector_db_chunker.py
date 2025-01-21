import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.chunking.chunker.base_chunker import BaseChunker
from app.common.services.chunking.document import Document, chunks_to_docs
from app.common.services.chunking.vector_store.main import ChunkVectorStoreManager
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients


class VectorDBChunker(BaseChunker):
    def __init__(
        self,
        local_repo: BaseLocalRepo,
        process_executor: ProcessPoolExecutor,
        weaviate_client: WeaviateSyncAndAsyncClients,
        embedding_manager: BaseEmbeddingManager,
        chunkable_files_and_hashes: Optional[Dict[str, str]] = None,
        use_new_chunking: bool = True,
    ):
        super().__init__(local_repo, process_executor)
        self.use_new_chunking = use_new_chunking
        self.weaviate_client = weaviate_client
        self.embedding_manager = embedding_manager
        self.chunkable_files_and_hashes = chunkable_files_and_hashes

    async def add_chunk_embeddings(self, chunks: List[ChunkInfo]) -> None:
        """
        Adds embeddings to the chunks.

        Args:
            chunks (List[ChunkInfo]): A list of chunks to which embeddings should be added.

        Returns:
            List[ChunkInfo]: A list of chunks with embeddings added.
        """
        texts_to_embed = [
            chunk.get_chunk_content_with_meta_data(add_ellipsis=False, add_lines=False, add_class_function_info=True)
            for chunk in chunks
        ]
        embeddings, _input_tokens = await self.embedding_manager.embed_text_array(texts=texts_to_embed)
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

    async def get_file_wise_chunks_for_single_file_batch(
        self,
        files_to_chunk_batch: List[Tuple[str, str]],
    ) -> Dict[str, List[ChunkInfo]]:
        """
        Handles a batch of files to be chunked
        """
        file_wise_chunks = await self.file_chunk_creator.create_and_get_file_wise_chunks(
            dict(files_to_chunk_batch),
            self.local_repo.repo_path,
            self.use_new_chunking,
            process_executor=self.process_executor,
        )

        batched_chunks: List[ChunkInfo] = []
        for chunks in file_wise_chunks.values():
            batched_chunks.extend(chunks)

        if batched_chunks:
            await self.add_chunk_embeddings(batched_chunks)
            await ChunkVectorStoreManager(
                local_repo=self.local_repo, weaviate_client=self.weaviate_client
            ).add_differential_chunks_to_store(file_wise_chunks)
        return file_wise_chunks

    def batchify_files_for_insertion(
        self, files_to_chunk: Dict[str, str], max_batch_size_chunking: int = 200
    ) -> List[List[Tuple[str, str]]]:
        files_to_chunk_items = list(files_to_chunk.items())
        batched_files_to_store: List[List[Tuple[str, str]]] = []
        for i in range(0, len(files_to_chunk), max_batch_size_chunking):
            # create batch chunks
            batch_files = files_to_chunk_items[i : i + max_batch_size_chunking]
            batched_files_to_store.append(batch_files)

        return batched_files_to_store

    async def create_and_store_chunks_for_file_batches(
        self,
        batched_files_to_store: List[List[Tuple[str, str]]],
    ) -> Dict[str, List[ChunkInfo]]:
        all_file_wise_chunks: Dict[str, List[ChunkInfo]] = {}
        for batch_files in batched_files_to_store:
            chunk_obj = await self.get_file_wise_chunks_for_single_file_batch(
                files_to_chunk_batch=batch_files,
            )
            all_file_wise_chunks.update(chunk_obj)

        return all_file_wise_chunks

    async def _update_chunk_and_chunk_files_timestamps(self, file_wise_chunks: Dict[str, List[ChunkInfo]]) -> None:
        """
        Updates the timestamp of the chunks and chunk files in the database.
        """
        max_batch_size = 1000
        for i in range(0, len(file_wise_chunks), max_batch_size):
            batch = list(file_wise_chunks.items())[i : i + max_batch_size]
            await ChunkVectorStoreManager(
                local_repo=self.local_repo, weaviate_client=self.weaviate_client
            ).add_differential_chunks_to_store(dict(batch))

    async def create_chunks_and_docs(self) -> Tuple[List[ChunkInfo], List[Document]]:
        """
        Converts the content of a list of files into chunks of code.

        Args:
            file_path (List[str]): A list of file paths to be processed.

        Returns:
            List[ChunkInfo]: A list of code chunks extracted from the files.
        """
        file_path_commit_hash_map = self.chunkable_files_and_hashes
        if not file_path_commit_hash_map:
            file_path_commit_hash_map = await self.local_repo.get_chunkable_files_and_commit_hashes()
        file_wise_chunk_files_and_chunks = await ChunkVectorStoreManager(
            weaviate_client=self.weaviate_client, local_repo=self.local_repo
        ).get_file_wise_stored_chunk_files_and_chunks(file_path_commit_hash_map)

        # only those files are valid which have all chunks stored
        valid_files_with_all_stored_chunks = {
            file_path
            for file_path, vector_store_file_and_chunk in file_wise_chunk_files_and_chunks.items()
            if len(vector_store_file_and_chunk) == vector_store_file_and_chunk[0][0].total_chunks
        }

        files_to_chunk = {
            file: file_hash
            for file, file_hash in file_path_commit_hash_map.items()
            if file not in valid_files_with_all_stored_chunks
        }
        batchified_files_for_insertion = self.batchify_files_for_insertion(
            files_to_chunk=files_to_chunk,
        )

        missing_file_wise_chunks: Dict[str, List[ChunkInfo]] = await self.create_and_store_chunks_for_file_batches(
            batchified_files_for_insertion
        )

        existing_file_wise_chunks = {
            file_path: [
                ChunkInfo(
                    content=vector_store_file[1].text,
                    source_details=ChunkSourceDetails(
                        file_path=vector_store_file[0].file_path,
                        file_hash=vector_store_file[0].file_hash,
                        start_line=vector_store_file[0].start_line,
                        end_line=vector_store_file[0].end_line,
                    ),
                    embedding=vector_store_file[2],
                )
                for vector_store_file in file_wise_chunk_files_and_chunks[file_path]
            ]
            for file_path in valid_files_with_all_stored_chunks
        }

        asyncio.create_task(self._update_chunk_and_chunk_files_timestamps(existing_file_wise_chunks))

        all_file_wise_chunks = {**missing_file_wise_chunks, **existing_file_wise_chunks}
        final_chunks: List[ChunkInfo] = []
        for chunks in all_file_wise_chunks.values():
            final_chunks.extend(chunks)

        return final_chunks, chunks_to_docs(final_chunks)
