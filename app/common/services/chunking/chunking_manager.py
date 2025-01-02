import os
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

from sanic.log import logger
from weaviate import WeaviateAsyncClient

from app.common.constants.constants import LLModels, PromptFeatures
from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.chunking.chunking_handler import (
    read_file,
    render_snippet_array,
)
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.llm.handler import LLMHandler
from app.common.services.prompt.factory import PromptFeatureFactory
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.services.search.search import perform_search
from app.main.blueprints.deputy_dev.services.setting_service import SettingService
from app.main.blueprints.deputy_dev.utils import is_path_included
from torpedo import CONFIG


class ChunkingManger:
    @classmethod
    async def sort_and_filter_chunks_by_heuristic(cls, ranked_snippets_list: List[ChunkInfo]) -> str:
        chunks_in_order = []
        source_to_chunks: Dict[str, List[ChunkInfo]] = {}
        for chunk in ranked_snippets_list:
            if chunk.source_details.file_path not in source_to_chunks:
                source_to_chunks[chunk.source_details.file_path] = []
            source_to_chunks[chunk.source_details.file_path].append(chunk)

        for source, chunks in source_to_chunks.items():
            chunks = sorted(chunks, key=lambda x: x.source_details.start_line)

            # remove chunks which are completely inside another chunk
            chunks = [
                chunk
                for i, chunk in enumerate(chunks)
                if not any(
                    chunk.source_details.start_line >= c.source_details.start_line
                    and chunk.source_details.end_line <= c.source_details.end_line
                    for c in chunks[:i] + chunks[i + 1 :]
                )
            ]
            chunks_in_order.extend(chunks)

        return render_snippet_array(chunks_in_order)

    @classmethod
    def build_focus_query(cls, user_query: str, custom_context_code_chunks: List[ChunkInfo]):
        if not custom_context_code_chunks:
            return user_query

        focus_query = f"{user_query}"
        for chunk in custom_context_code_chunks:
            focus_query += f"\n{chunk.content}"
        return focus_query

    @classmethod
    async def get_custom_context_chunks_from_focus_files(
        cls,
        focus_file_paths: List[str],
        user_query: str,
        local_repo: BaseLocalRepo,
        custom_context_code_chunks: List[ChunkInfo],
        chunkable_files_with_hashes: Dict[str, str],
        embedding_manager: BaseEmbeddingManager,
        process_executor: ProcessPoolExecutor,
        query_vector: Optional[List[float]] = None,
        use_llm_context: bool = False,
        use_new_chunking: bool = False,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateAsyncClient] = None,
    ):
        # custom_context_chunks: List[ChunkInfo] = []
        # focus_file_abs_paths = [os.path.join(local_repo.repo_path, file_path) for file_path in focus_file_paths]
        # for file_path in focus_file_abs_paths:
        #     custom_context_chunks.extend(
        #         create_chunks(
        #             file_path=file_path,
        #             root_dir=local_repo.repo_path,
        #             file_hash="",
        #             use_new_chunking=use_new_chunking,
        #         )
        #     )

        # custom_context_docs = chunks_to_docs(custom_context_chunks)

        sorted_chunks, _ = await perform_search(
            query=cls.build_focus_query(user_query, custom_context_code_chunks),
            local_repo=local_repo,
            use_new_chunking=use_new_chunking,
            search_type=search_type,
            embedding_manager=embedding_manager,
            process_executor=process_executor,
            chunkable_files_with_hashes=chunkable_files_with_hashes,
            query_vector=query_vector,
            weaviate_client=weaviate_client,
        )

        return custom_context_code_chunks + sorted_chunks

    @classmethod
    async def get_custom_context_chunks_from_focus_code_chunks(
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
        use_llm_context: bool = False,
        use_new_chunking: bool = False,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateAsyncClient] = None,
    ) -> List[ChunkInfo]:
        user_defined_chunks = []
        if custom_context_code_chunks:
            user_defined_chunks = await cls.get_custom_context_chunks_from_focus_code_chunks(
                custom_context_code_chunks, local_repo
            )
        if custom_context_files:
            return await cls.get_custom_context_chunks_from_focus_files(
                custom_context_files,
                query,
                local_repo,
                user_defined_chunks,
                chunkable_files_with_hashes,
                embedding_manager,
                process_executor,
                query_vector,
                use_llm_context,
                use_new_chunking,
                search_type=search_type,
                weaviate_client=weaviate_client,
            )
        else:
            return user_defined_chunks

    @classmethod
    async def get_related_chunk_from_codebase_repo(
        cls,
        query: str,
        local_repo: BaseLocalRepo,
        custom_context_files: List[str],
        focus_chunks: List[ChunkInfo],
        chunkable_files_with_hashes: Dict[str, str],
        embedding_manager: BaseEmbeddingManager,
        process_executor: ProcessPoolExecutor,
        query_vector: Optional[List[float]] = None,
        use_llm_context: bool = False,
        use_new_chunking: bool = False,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateAsyncClient] = None,
    ) -> Tuple[List[ChunkInfo], int]:

        logger.info("Completed chunk creation")
        if focus_chunks:
            query = cls.build_focus_query(query, focus_chunks)

        sorted_chunks, input_tokens = await perform_search(
            query=query,
            local_repo=local_repo,
            query_vector=query_vector,
            chunkable_files_with_hashes=chunkable_files_with_hashes,
            use_new_chunking=use_new_chunking,
            search_type=search_type,
            embedding_manager=embedding_manager,
            process_executor=process_executor,
            weaviate_client=weaviate_client,
        )

        return sorted_chunks, input_tokens

    @classmethod
    async def sort_and_filter_chunks_by_llm(
        cls, focus_chunks: List[ChunkInfo], related_chunk: List[ChunkInfo], query: str
    ) -> str:
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.RE_RANKING,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={
                "query": query,
                "focus_chunks": render_snippet_array(focus_chunks),
                "related_chunk": render_snippet_array(related_chunk),
            },
        )
        llm_response = await LLMHandler(prompt=prompt).get_llm_response_data(previous_responses=[])
        return llm_response.parsed_llm_data["filtered_chunks"]

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
        use_llm_re_ranking: bool = True,
        use_new_chunking: bool = True,
        search_type: SearchTypes = SearchTypes.VECTOR_DB_BASED,
        weaviate_client: Optional[WeaviateAsyncClient] = None,
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
            use_llm_re_ranking,
            use_new_chunking,
            search_type=search_type,
            weaviate_client=weaviate_client,
        )
        if only_focus_code_chunks and focus_chunks_details:
            return render_snippet_array(focus_chunks_details), 0

        related_chunk, input_tokens = await cls.get_related_chunk_from_codebase_repo(
            query,
            local_repo,
            focus_files,
            focus_chunks_details,
            chunkable_files_with_hashes,
            embedding_manager,
            process_executor,
            query_vector,
            use_llm_re_ranking,
            use_new_chunking,
            search_type=search_type,
            weaviate_client=weaviate_client,
        )
        # filter out the focus chunks from the related chunks if any, based on content
        related_chunk = [
            chunk for chunk in related_chunk if chunk.content not in [chunk.content for chunk in focus_chunks_details]
        ]
        # TODO: will update this after code finalization of relevant chunks
        return cls.agent_wise_relevant_chunks(related_chunk), input_tokens
        # if not use_llm_re_ranking:
        #     return await cls.sort_and_filter_chunks_by_heuristic(focus_chunks_details + related_chunk), input_tokens
        # else:
        #     return await cls.sort_and_filter_chunks_by_llm(focus_chunks_details, related_chunk, query), input_tokens

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
