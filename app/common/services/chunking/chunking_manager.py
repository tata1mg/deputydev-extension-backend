import os
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from sanic.log import logger
from torpedo import CONFIG

from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.chunking.chunker.base_chunker import BaseChunker
from app.common.services.chunking.reranker.base_chunk_reranker import BaseChunkReranker
from app.common.services.chunking.reranker.handlers.heuristic_based import (
    HeuristicBasedChunkReranker,
)
from app.common.services.chunking.utils.snippet_renderer import render_snippet_array
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.services.search.search import perform_search
from app.common.utils.file_utils import read_file
from app.main.blueprints.deputy_dev.services.workspace.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.utils import is_path_included


class ChunkingManger:
    @classmethod
    def build_focus_query(cls, user_query: str, custom_context_code_chunks: List[ChunkInfo]):
        if not custom_context_code_chunks:
            return user_query

        focus_query = f"{user_query}"
        for chunk in custom_context_code_chunks:
            focus_query += f"\n{chunk.content}"
        return focus_query

    @classmethod
    async def get_relevant_context_from_focus_files(
        cls,
        focus_file_paths: List[str],
        user_query: str,
        custom_context_code_chunks: List[ChunkInfo],
        chunkable_files_with_hashes: Dict[str, str],
        embedding_manager: BaseEmbeddingManager,
        process_executor: ProcessPoolExecutor,
        query_vector: Optional[List[float]] = None,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None,
        usage_hash: Optional[str] = None,
        chunking_handler: Optional[BaseChunker] = None,
    ):
        filtered_files = {file_path: chunkable_files_with_hashes[file_path] for file_path in focus_file_paths}

        sorted_chunks, _ = await perform_search(
            query=cls.build_focus_query(user_query, custom_context_code_chunks),
            search_type=search_type,
            embedding_manager=embedding_manager,
            process_executor=process_executor,
            chunkable_files_with_hashes=filtered_files,
            query_vector=query_vector,
            weaviate_client=weaviate_client,
            usage_hash=usage_hash,
            chunking_handler=chunking_handler,
        )
        return custom_context_code_chunks + sorted_chunks

    @classmethod
    async def get_relevant_context_from_focus_snippets(
        cls, focus_code_chunks: List[str], local_repo: BaseLocalRepo
    ) -> List[ChunkInfo]:
        custom_context_chunks: List[ChunkInfo] = []
        for focus_code_chunk in focus_code_chunks:
            filepath, lines = focus_code_chunk.split(":")
            lines = lines.split("-")
            abs_filepath = os.path.join(local_repo.repo_path, filepath)
            file_content = read_file(abs_filepath)
            custom_context_chunks.append(
                ChunkInfo(
                    content=file_content,
                    source_details=ChunkSourceDetails(
                        file_path=abs_filepath, file_hash="", start_line=int(lines[0]), end_line=int(lines[1])
                    ),
                )
            )
        return custom_context_chunks

    @classmethod
    async def get_focus_chunk(
        cls,
        query: str,
        local_repo: BaseLocalRepo,
        custom_context_files: List[str],
        custom_context_code_chunks: List[str],
        chunkable_files_with_hashes: Dict[str, str],
        embedding_manager: BaseEmbeddingManager,
        process_executor: ProcessPoolExecutor,
        query_vector: Optional[List[float]] = None,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None,
        usage_hash: Optional[str] = None,
        chunking_handler: Optional[BaseChunker] = None,
    ) -> List[ChunkInfo]:
        user_defined_chunks = []
        if custom_context_code_chunks:
            user_defined_chunks = await cls.get_relevant_context_from_focus_snippets(
                custom_context_code_chunks, local_repo
            )
        if custom_context_files:
            return await cls.get_relevant_context_from_focus_files(
                custom_context_files,
                query,
                user_defined_chunks,
                chunkable_files_with_hashes,
                embedding_manager,
                process_executor,
                query_vector,
                search_type=search_type,
                weaviate_client=weaviate_client,
                usage_hash=usage_hash,
                chunking_handler=chunking_handler,
            )
        else:
            return user_defined_chunks

    @classmethod
    async def get_related_chunk_from_codebase_repo(
        cls,
        query: str,
        focus_chunks: List[ChunkInfo],
        chunkable_files_with_hashes: Dict[str, str],
        embedding_manager: BaseEmbeddingManager,
        process_executor: ProcessPoolExecutor,
        query_vector: Optional[List[float]] = None,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None,
        usage_hash: Optional[str] = None,
        chunking_handler: Optional[BaseChunker] = None,
        agent_wise_chunks=False,
    ) -> Tuple[List[ChunkInfo], int]:

        logger.info("Completed chunk creation")
        if focus_chunks:
            query = cls.build_focus_query(query, focus_chunks)

        sorted_chunks, input_tokens = await perform_search(
            query=query,
            query_vector=query_vector,
            chunkable_files_with_hashes=chunkable_files_with_hashes,
            search_type=search_type,
            chunking_handler=chunking_handler,
            embedding_manager=embedding_manager,
            process_executor=process_executor,
            weaviate_client=weaviate_client,
            usage_hash=usage_hash,
            agent_wise_chunks=False,
        )

        return sorted_chunks, input_tokens

    @classmethod
    async def get_relevant_chunks(
        cls,
        query: str,
        chunkable_files_with_hashes: Dict[str, str],
        local_repo: BaseLocalRepo,
        embedding_manager: BaseEmbeddingManager,
        process_executor: ProcessPoolExecutor,
        focus_files: List[str] = [],
        focus_chunks: List[str] = [],
        query_vector: Optional[List[float]] = None,
        only_focus_code_chunks: bool = False,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None,
        usage_hash: Optional[str] = None,
        chunking_handler: Optional[BaseChunker] = None,
        reranker: Optional[BaseChunkReranker] = None,
        agent_wise_chunks=False,
    ) -> Tuple[str, int]:
        # Get all chunks from the repository
        focus_chunks_details = await cls.get_focus_chunk(
            query,
            local_repo,
            focus_files,
            focus_chunks,
            chunkable_files_with_hashes,
            embedding_manager,
            process_executor,
            query_vector,
            search_type=search_type,
            weaviate_client=weaviate_client,
            usage_hash=usage_hash,
            chunking_handler=chunking_handler,
        )
        if only_focus_code_chunks and focus_chunks_details:
            return render_snippet_array(focus_chunks_details), 0

        related_chunk, input_tokens = await cls.get_related_chunk_from_codebase_repo(
            query,
            focus_chunks_details,
            chunkable_files_with_hashes,
            embedding_manager,
            process_executor,
            query_vector,
            search_type=search_type,
            weaviate_client=weaviate_client,
            usage_hash=usage_hash,
            chunking_handler=chunking_handler,
            agent_wise_chunks=agent_wise_chunks
        )
        # filter out the focus chunks from the related chunks if any, based on content
        related_chunk = [
            chunk for chunk in related_chunk if chunk.content not in [chunk.content for chunk in focus_chunks_details]
        ]

        reranker_to_use = reranker or HeuristicBasedChunkReranker()
        reranked_chunks = await reranker_to_use.rerank(focus_chunks_details, related_chunk, query)

        return render_snippet_array(reranked_chunks), input_tokens

    @classmethod
    def agent_wise_relevant_chunks(cls, ranked_snippets_list):
        NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]
        agents = SettingService.get_uuid_wise_agents()
        remaining_agents = len(agents)

        relevant_chunks = {agent_id: [] for agent_id in agents}

        for snippet in ranked_snippets_list:
            if remaining_agents == 0:
                break

            path = snippet.denotation

            for agent_id, agent_info in agents.items():
                # Skip if the agent already has the required number of chunks
                if len(relevant_chunks[agent_id]) >= NO_OF_CHUNKS:
                    continue

                inclusions, exclusions = SettingService.get_agent_inclusion_exclusions(agent_id)

                # Check if the path is relevant
                if is_path_included(path, exclusions, inclusions):
                    relevant_chunks[agent_id].append(snippet)

                    # Decrement the counter when the agent reaches the chunk limit
                    if len(relevant_chunks[agent_id]) == NO_OF_CHUNKS:
                        remaining_agents -= 1

                        # Exit the loop early if all agents are fulfilled
                        if remaining_agents == 0:
                            break

        return relevant_chunks
