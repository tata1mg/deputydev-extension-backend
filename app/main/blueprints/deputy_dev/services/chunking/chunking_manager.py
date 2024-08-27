from sanic.log import logger
from torpedo import CONFIG

from app.main.blueprints.deputy_dev.services.chunking.chunk_parsing_utils import (
    get_chunks,
    render_snippet_array,
)
from app.main.blueprints.deputy_dev.services.search import perform_search


class ChunkingManger:
    NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]

    @classmethod
    async def get_relevant_chunk(cls, repo):
        # clone the repo
        all_chunks, all_docs = await get_chunks(repo.repo_dir)
        logger.info("Completed chunk creation")

        # Perform a search based on the diff content to find relevant chunks
        content_to_lexical_score_list, input_tokens = await perform_search(
            all_docs=all_docs, all_chunks=all_chunks, query=repo.pr_diff
        )
        logger.info("Completed lexical and vector search")

        # Rank relevant chunks based on lexical scores
        ranked_snippets_list = sorted(
            all_chunks,
            key=lambda chunk: content_to_lexical_score_list[chunk.denotation],
            reverse=True,
        )[: cls.NO_OF_CHUNKS]

        # Render relevant chunks into a single snippet
        relevant_chunk = render_snippet_array(ranked_snippets_list)
        return relevant_chunk, input_tokens
