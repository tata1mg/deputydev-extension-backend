from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from app.common.services.chunking.chunker.base_chunker import BaseChunker
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.services.search.native.search import NativeSearch
from app.common.services.search.vector_db_based.search import VectorDBBasedSearch

from ..chunking.chunk_info import ChunkInfo


async def perform_search(
    query: str,
    chunkable_files_with_hashes: Dict[str, str],
    search_type: SearchTypes,
    embedding_manager: BaseEmbeddingManager,
    process_executor: ProcessPoolExecutor,
    chunking_handler: Optional[BaseChunker] = None,
    query_vector: Optional[List[float]] = None,
    weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None,
    usage_hash: Optional[str] = None,
    agent_wise_chunks: Optional[bool] = False,
) -> Tuple[List[ChunkInfo], int]:

    sorted_chunks: List[ChunkInfo] = []
    input_tokens: int = 0
    if search_type == SearchTypes.NATIVE:
        if not chunking_handler:
            raise ValueError("Chunking handler is required for native search")
        sorted_chunks, input_tokens = await NativeSearch.perform_search(
            query=query,
            embedding_manager=embedding_manager,
            process_executor=process_executor,
            chunking_handler=chunking_handler,
        )
        return sorted_chunks, input_tokens
    elif search_type == SearchTypes.VECTOR_DB_BASED:
        if not weaviate_client:
            raise ValueError("Weaviate client is required for vector db based search")
        if query_vector is None:
            raise ValueError("Query vector is required for vector db based search")
        if not chunkable_files_with_hashes:
            raise ValueError("Chunkable files with hashes are required for vector db based search")
        if not usage_hash:
            raise ValueError("Usage hash is required for vector db based search")
        sorted_chunks, input_tokens = await VectorDBBasedSearch.perform_search(
            whitelisted_file_commits=chunkable_files_with_hashes,
            query=query,
            query_vector=query_vector,
            weaviate_client=weaviate_client,
            usage_hash=usage_hash,
        )

    return sorted_chunks, input_tokens
