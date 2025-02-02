from typing import Dict, List, Tuple

from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.repository.chunk.chunk_service import ChunkService
from app.common.services.repository.chunk_files.chunk_files_service import (
    ChunkFilesService,
)
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients


class VectorDBBasedSearch:
    @classmethod
    async def perform_search(
        cls,
        whitelisted_file_commits: Dict[str, str],
        query: str,
        query_vector: List[float],
        weaviate_client: WeaviateSyncAndAsyncClients,
        max_chunks_to_return: int,
    ) -> Tuple[List[ChunkInfo], int]:

        chunk_files = await ChunkFilesService(weaviate_client).get_chunk_files_by_commit_hashes(
            whitelisted_file_commits
        )
        chunk_hashes = [chunk_file.chunk_hash for chunk_file in chunk_files]

        sorted_chunk_dtos = await ChunkService(weaviate_client).perform_filtered_vector_hybrid_search(
            chunk_hashes=chunk_hashes, query=query, query_vector=query_vector, limit=max_chunks_to_return
        )

        # merge chunk files and chunk dtos
        chunk_info_list: List[ChunkInfo] = []
        for chunk_dto in sorted_chunk_dtos:
            for chunk_file in chunk_files:
                if chunk_file.chunk_hash == chunk_dto.chunk.chunk_hash:
                    chunk_info_list.append(
                        ChunkInfo(
                            content=chunk_dto.chunk.text,
                            source_details=ChunkSourceDetails(
                                file_path=chunk_file.file_path,
                                file_hash=chunk_file.file_hash,
                                start_line=chunk_file.start_line,
                                end_line=chunk_file.end_line,
                            ),
                            embedding=None,
                            search_score=chunk_dto.score,
                        )
                    )
                    break

        return chunk_info_list, 0
