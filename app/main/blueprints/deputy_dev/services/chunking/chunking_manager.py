from sanic.log import logger
from torpedo import CONFIG

from app.main.blueprints.deputy_dev.services.chunking.chunk_parsing_utils import (
    get_chunks,
    render_snippet_array,
)
from app.main.blueprints.deputy_dev.services.search import perform_search
from app.main.blueprints.deputy_dev.services.setting_service import SettingService
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import is_path_included


class ChunkingManger:
    NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]

    @classmethod
    async def get_relevant_chunk(cls, repo):
        # clone the repo
        all_chunks, all_docs = await get_chunks(repo.repo_dir)
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
