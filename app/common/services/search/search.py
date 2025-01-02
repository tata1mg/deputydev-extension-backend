from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from weaviate import WeaviateAsyncClient

from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.services.search.native.search import NativeSearch
from app.common.services.search.vector_db_based.search import VectorDBBasedSearch

from ..chunking.chunk_info import ChunkInfo


async def perform_search(
    query: str,
    chunkable_files_with_hashes: Dict[str, str],
    local_repo: BaseLocalRepo,
    search_type: SearchTypes,
    embedding_manager: BaseEmbeddingManager,
    process_executor: ProcessPoolExecutor,
    query_vector: Optional[List[float]] = None,
    use_new_chunking: bool = True,
    weaviate_client: Optional[WeaviateAsyncClient] = None,
) -> Tuple[List[ChunkInfo], int]:

    sorted_chunks: List[ChunkInfo] = []
    input_tokens: int = 0
    if search_type == SearchTypes.NATIVE:
        sorted_chunks, input_tokens = await NativeSearch.perform_search(
            query=query,
            local_repo=local_repo,
            embedding_manager=embedding_manager,
            use_new_chunking=use_new_chunking,
            process_executor=process_executor,
        )
    elif search_type == SearchTypes.VECTOR_DB_BASED:
        if not weaviate_client:
            raise ValueError("Weaviate client is required for vector db based search")
        if query_vector is None:
            raise ValueError("Query vector is required for vector db based search")
        if not chunkable_files_with_hashes:
            raise ValueError("Chunkable files with hashes are required for vector db based search")
        sorted_chunks, input_tokens = await VectorDBBasedSearch.perform_search(
            whitelisted_file_commits=chunkable_files_with_hashes,
            query=query,
            query_vector=query_vector,
            weaviate_client=weaviate_client,
        )

    return sorted_chunks, input_tokens
