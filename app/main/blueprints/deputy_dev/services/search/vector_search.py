import asyncio
from typing import Dict, List, Tuple

import numpy as np

from app.common.services.openai.client import LLMClient
from app.common.utils.executor import executor
from app.main.blueprints.deputy_dev.constants import BATCH_SIZE
from app.main.blueprints.deputy_dev.services.chunking.chunk_info import ChunkInfo


async def embed_text_array(texts: Tuple[str]) -> (List[np.ndarray], int):
    """
    Embeds a list of texts using OpenAI's embedding model.

    Args:
        texts (tuple[str]): A tuple of texts to embed.

    Returns:
        list[np.ndarray]: List of embeddings for each text.
    """
    embeddings = []
    input_tokens = 0
    texts = [text if text else " " for text in texts]
    batches = [texts[i : i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
    for batch in batches:
        embedding, input_token = await LLMClient().get_embeddings(batch)
        embeddings.append(embedding)
    return embeddings, input_tokens


def cosine_similarity(a: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Calculates the cosine similarity between two vectors.

    Args:
        a (np.ndarray): The first vector.
        B (np.ndarray): The second vector or matrix of vectors.

    Returns:
        np.ndarray: Array of cosine similarities.
    """
    dot_product = np.dot(B, a.T)
    norm_a = np.linalg.norm(a)
    norm_B = np.linalg.norm(B, axis=1)
    return dot_product.flatten() / (norm_a * norm_B)


async def get_query_texts_similarity(query: str, texts: List[str]) -> (List[float], int):
    """
    Computes the cosine similarity between a query and a list of texts.

    Args:
        query (str): The query text.
        texts (list[str]): List of texts to compare against the query.

    Returns:
        list[float]: List of cosine similarity scores.
    """
    if not texts:
        return [], None
    embeddings, input_tokens = await embed_text_array(texts)
    embeddings = np.concatenate(embeddings)
    query_embedding, input_tokens = await LLMClient().get_embeddings([query])
    similarity = cosine_similarity(query_embedding, embeddings)
    similarity = similarity.tolist()
    return similarity, input_tokens


def create_chunk_str_to_contents(chunks: List[ChunkInfo]) -> Dict[str, str]:
    """
    Creates a dictionary mapping chunk denotations to their content.

    This function iterates over a list of ChunkInfo objects and constructs a
    dictionary where the keys are the denotations of the chunks and the values
    are the content of the chunks obtained by calling the get_chunk_content method.

    Args:
        chunks (List[ChunkInfo]): A list of ChunkInfo objects.

    Returns:
        Dict[str, str]: A dictionary mapping each chunk's denotation to its content.
    """
    return {chunk.denotation: chunk.get_chunk_content(add_ellipsis=False, add_lines=False) for chunk in chunks}


async def compute_vector_search_scores(query: str, chunks: List[ChunkInfo]) -> dict:
    """
    Computes vector search scores for a query and a list of ChunkInfo objects.

    Args:
        query (str): The query string.
        chunks (list[ChunkInfo]): List of ChunkInfo objects representing text chunks.

    Returns:
        dict: Dictionary mapping chunk denotations to similarity scores.
    """
    # Instantiate an event loop object for main thread
    loop = asyncio.get_event_loop()
    # Create a ProcessPoolExecutor
    chunk_str_to_contents = await loop.run_in_executor(executor, create_chunk_str_to_contents, chunks)
    chunk_contents_array = list(chunk_str_to_contents.values())
    query_snippet_similarities, input_tokens = await get_query_texts_similarity(query, chunk_contents_array)
    chunk_denotations = [chunk.denotation for chunk in chunks]
    chunk_denotation_to_scores = {chunk_denotations[i]: score for i, score in enumerate(query_snippet_similarities)}
    return chunk_denotation_to_scores, input_tokens
