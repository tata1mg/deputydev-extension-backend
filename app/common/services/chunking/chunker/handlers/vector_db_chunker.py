from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.chunking.chunker.base_chunker import BaseChunker
from app.common.services.chunking.document import Document, chunks_to_docs
from app.common.services.chunking.vector_store.main import ChunkVectorScoreManager
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
        usage_hash: str,
        chunkable_files_and_hashes: Optional[Dict[str, str]] = None,
        use_new_chunking: bool = True,
    ):
        super().__init__(local_repo, process_executor)
        self.use_new_chunking = use_new_chunking
        self.weaviate_client = weaviate_client
        self.embedding_manager = embedding_manager
        self.usage_hash = usage_hash
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
            await self.add_chunk_embeddings(batched_chunks)
            await ChunkVectorScoreManager(
                local_repo=self.local_repo, weaviate_client=self.weaviate_client
            ).add_differential_chunks_to_store(batched_chunks, usage_hash=self.usage_hash)
        return batched_chunks

    def batchify_chunks_for_insertion(
        self, files_to_chunk: Dict[str, str], max_batch_size_chunking: int = 1000
    ) -> List[List[Tuple[str, str]]]:
        files_to_chunk_items = list(files_to_chunk.items())
        batched_files_to_store: List[List[Tuple[str, str]]] = []
        for i in range(0, len(files_to_chunk), max_batch_size_chunking):
            # create batch chunks
            batch_files = files_to_chunk_items[i : i + max_batch_size_chunking]
            batched_files_to_store.append(batch_files)

        return batched_files_to_store

    async def batch_chunk_inserter(
        self,
        batched_files_to_store: List[List[Tuple[str, str]]],
    ) -> List[ChunkInfo]:
        all_chunks: List[ChunkInfo] = []
        for batch_files in batched_files_to_store:
            chunk_obj = await self.handle_chunking_batch(
                files_to_chunk_batch=batch_files,
            )
            all_chunks.extend(chunk_obj)

        return all_chunks

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
        vector_store_files_and_chunks = await ChunkVectorScoreManager(
            weaviate_client=self.weaviate_client, local_repo=self.local_repo
        ).get_stored_chunk_files_with_chunk_content(file_path_commit_hash_map)
        existing_files = {vector_file[0].file_path for vector_file in vector_store_files_and_chunks}

        files_to_chunk = {
            file: file_hash for file, file_hash in file_path_commit_hash_map.items() if file not in existing_files
        }
        batchified_chunks_for_insertion = self.batchify_chunks_for_insertion(
            files_to_chunk=files_to_chunk,
        )
        final_chunks: List[ChunkInfo] = await self.batch_chunk_inserter(batchified_chunks_for_insertion)
        final_chunks.extend(
            [
                ChunkInfo(
                    content=vector_store_file[1].text,
                    source_details=ChunkSourceDetails(
                        file_path=vector_store_file[0].file_path,
                        file_hash=vector_store_file[0].file_hash,
                        start_line=vector_store_file[0].start_line,
                        end_line=vector_store_file[0].end_line,
                    ),
                )
                for vector_store_file in vector_store_files_and_chunks
            ]
        )

        return final_chunks, chunks_to_docs(final_chunks)
