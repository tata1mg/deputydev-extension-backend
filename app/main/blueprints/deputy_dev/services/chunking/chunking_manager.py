import re
from typing import List

from sanic.log import logger
from torpedo import CONFIG

from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.services.chunking.chunk_info import ChunkInfo
from app.main.blueprints.deputy_dev.services.chunking.chunk_parsing_utils import (
    get_chunks,
    render_snippet_array,
)
from app.main.blueprints.deputy_dev.services.llm.anthropic_llm import Anthropic
from app.main.blueprints.deputy_dev.services.search import perform_search
from app.main.blueprints.deputy_dev.services.setting_service import SettingService
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import is_path_included


class ChunkingManger:
    NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]

    @classmethod
    async def get_relevant_chunk(cls, repo, use_new_chunking=False, use_llm_re_ranking=False):
        # clone the repo
        all_chunks, all_docs = await get_chunks(repo.repo_dir, use_new_chunking)
        logger.info("Completed chunk creation")
        query = repo.get_effective_pr_diff()
        # Perform a search based on the diff content to find relevant chunks
        content_to_lexical_score_list, input_tokens = await perform_search(
            all_docs=all_docs, all_chunks=all_chunks, query=query
        )
        logger.info("Completed lexical and vector search")

        # Rank relevant chunks based on lexical scores
        ranked_snippets_list = sorted(
            all_chunks,
            key=lambda chunk: content_to_lexical_score_list[chunk.denotation],
            reverse=True,
        )
        relevant_chunks_lists = cls.agent_wise_relevant_chunks(ranked_snippets_list)
        relevant_chunks_single_snippet = {}
        for agent_id, chunks in relevant_chunks_lists.items():
            # Render relevant chunks into a single snippet
            relevant_chunks_single_snippet[agent_id] = render_snippet_array(chunks)
        return relevant_chunks_single_snippet, input_tokens

    @classmethod
    def agent_wise_relevant_chunks(cls, ranked_snippets_list):
        agents = SettingService.get_uuid_wise_agents()
        remaining_agents = len(agents)

        relevant_chunks = {agent_id: [] for agent_id in agents}

        for snippet in ranked_snippets_list:
            if remaining_agents == 0:
                break

            path = snippet.denotation

            for agent_id, agent_info in agents.items():
                # Skip if the agent already has the required number of chunks
                if len(relevant_chunks[agent_id]) >= cls.NO_OF_CHUNKS:
                    continue

                inclusions, exclusions = SettingService.get_agent_inclusion_exclusions(agent_id)

                # Check if the path is relevant
                if is_path_included(path, exclusions, inclusions):
                    relevant_chunks[agent_id].append(snippet)

                    # Decrement the counter when the agent reaches the chunk limit
                    if len(relevant_chunks[agent_id]) == cls.NO_OF_CHUNKS:
                        remaining_agents -= 1

                        # Exit the loop early if all agents are fulfilled
                        if remaining_agents == 0:
                            break

        return relevant_chunks

    @classmethod
    async def sort_and_filter_chunks_by_heuristic(cls, ranked_snippets_list: List[ChunkInfo]) -> str:
        chunks_in_order = []
        source_to_chunks = {}
        for chunk in ranked_snippets_list:
            if chunk.source not in source_to_chunks:
                source_to_chunks[chunk.source] = []
            source_to_chunks[chunk.source].append(chunk)

        for source, chunks in source_to_chunks.items():
            chunks = sorted(chunks, key=lambda x: x.start)

            # remove chunks which are completely inside another chunk
            chunks = [
                chunk
                for i, chunk in enumerate(chunks)
                if not any(chunk.start >= c.start and chunk.end <= c.end for c in chunks[:i] + chunks[i + 1 :])
            ]
            chunks_in_order.extend(chunks)

        return render_snippet_array(chunks_in_order)

    @classmethod
    async def sort_chunks(cls, query, ranked_snippets_list, use_llm_re_ranking, focus_chunks=None):
        related_chunk = [
            chunk
            for chunk in ranked_snippets_list
            if chunk.content not in [chunk.content for chunk in focus_chunks or []]
        ]
        if use_llm_re_ranking:
            llm_ranked_snippet = await cls.sort_and_filter_chunks_by_llm(focus_chunks, related_chunk, query)
            if not llm_ranked_snippet:
                AppLogger.log_error("No snippet were received from llm")
            return llm_ranked_snippet
        else:
            return render_snippet_array(related_chunk)

    @classmethod
    async def sort_and_filter_chunks_by_llm(
        cls, focus_chunks: List[ChunkInfo], related_chunk: List[ChunkInfo], query: str
    ) -> str:
        def get_focus_chunk_prompt(f_chunks):
            return (
                f"""Here are the chunks that are taken from the files/snippets the user has explicitly mentioned:
                {render_snippet_array(f_chunks)}"""
                if f_chunks
                else ""
            )

        prompt = {
            "user_message": f"""
                Please sort and filter the following chunks based on the user's query, so that it can be used as a context for a LLM to answer the query.
                The user query is as follows -
                <user_query>{query}</user_query>
    
                <important>Please do check and ensure that you keep most of the chunks that are relevant. If one function is selected, keep all chunks related to that function.</important>
    
                {get_focus_chunk_prompt(focus_chunks)}
                Here are the related chunks found by similarity search from the codebase:
                {render_snippet_array(related_chunk)}
    
                Please send the sorted and filtered chunks in the following format:
                <important> Keep all the chunks that are relevant to the user query, do not be too forceful in removing out context</important>
                Please preserve line numbers, source and other metadata of the chunks passed.
                <sorted_and_filtered_chunks>
                <chunk>content1</chunk>
                <chunk>content2</chunk>
                ...
                </sorted_and_filtered_chunks>
                """,
            "system_message": "You are a codebase expert",
        }
        llm_response = await cls.get_llm_response(prompt, [])
        chunks_match = re.search(
            r"<sorted_and_filtered_chunks>(.*?)</sorted_and_filtered_chunks>", llm_response, re.DOTALL
        )
        if chunks_match:
            chunks_content = chunks_match.group(1).strip()
            return chunks_content or ""
        return ""

    @classmethod
    async def get_llm_response(cls, prompt, previous_responses):
        client = Anthropic()
        model_name = CONFIG.config.get("FEATURE_MODELS").get("RE_RANKING")
        model_config = CONFIG.config.get("LLM_MODELS").get(model_name)

        llm_message = client.build_llm_message(prompt, previous_responses)
        response = await client.call_service_client(
            messages=llm_message, model=model_config.get("NAME"), response_type="text"
        )

        parsed_response, _, _ = await client.parse_response(response)
        return parsed_response
