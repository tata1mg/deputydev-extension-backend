import asyncio
from typing import Any, Dict, List

from app.modules.chunking.chunk_info import ChunkInfo
from app.modules.chunking.document import Document
from app.modules.executor import executor

from .lexical_search import create_lexical_search_tokens, perform_lexical_search
from .vector_search import compute_vector_search_scores


async def create_tokens(all_docs: List[Document]):
    """
    Asynchronously creates lexical search tokens from a list of documents.

    This function uses a ProcessPoolExecutor to offload the token creation
    process to a separate process, thus avoiding blocking the main event loop.

    Args:
        all_docs (List[Document]): A list of Document objects to process.

    Returns:
        index: The result of the token creation process.
    """
    # Instantiate an event loop object for main thread
    loop = asyncio.get_event_loop()

    index = await loop.run_in_executor(executor, create_lexical_search_tokens, all_docs)

    return index


async def lexical_search(query: str, index: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Asynchronously performs a lexical search on the provided index using the given query.

    This function uses a ProcessPoolExecutor to offload the search process to a
    separate process, thus avoiding blocking the main event loop.

    Args:
        query (str): The search query string.
        index (Dict[str, Any]): The index to search against, typically a dictionary
                                containing precomputed lexical tokens and their positions.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the content and
                              their corresponding lexical scores.
    """
    # Instantiate an event loop object for main thread
    loop = asyncio.get_event_loop()

    content_to_lexical_score_list = await loop.run_in_executor(executor, perform_lexical_search, query, index)
    return content_to_lexical_score_list


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
    # create tokens for search
    index = await create_tokens(all_docs)
    # Perform lexical search
    content_to_lexical_score_list = await lexical_search(query, index)
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
