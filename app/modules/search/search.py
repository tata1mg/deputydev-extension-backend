from typing import Dict, List

from app.modules.chunking.chunk_info import ChunkInfo
from app.modules.chunking.document import Document

from .lexical_search import create_lexical_search_tokens, perform_lexical_search
from .vector_search import compute_vector_search_scores


async def perform_search(all_docs: List[Document], all_chunks: List[ChunkInfo], query: str) -> Dict[int, float]:
    """
    Perform a search operation on documents and document chunks.

    Args:
        all_docs (List[Document]): List of all documents.
        all_chunks (List[ChunkInfo]): List of all document chunks.
        query (Query): Search query.

    Returns:
        Dict[int, float]: Search results containing scores for each document chunk.
    """
    # Create lexical search index
    index = create_lexical_search_tokens(all_docs)
    # Perform lexical search
    content_to_lexical_score_list = perform_lexical_search(query, index)

    # Compute vector search scores asynchronously
    files_to_scores_list = await compute_vector_search_scores(query, all_chunks)

    # Calculate scores for each chunk
    for chunk in all_chunks:
        # Default values for scores
        vector_score = files_to_scores_list.get(chunk.denotation, 0.04)
        chunk_score = 0.02

        # Adjust chunk score if denotation is found in lexical search results
        if chunk.denotation in content_to_lexical_score_list:
            chunk_score = content_to_lexical_score_list[chunk.denotation] + (vector_score * 3.5)
            content_to_lexical_score_list[chunk.denotation] = chunk_score
        else:
            # If denotation not found, calculate score based on vector search only
            content_to_lexical_score_list[chunk.denotation] = chunk_score * vector_score
    # Return search results
    return content_to_lexical_score_list
