import json
import multiprocessing
from typing import List, Tuple

import numpy as np
import requests
from openai import OpenAI
from sanic.log import logger
from torpedo import CONFIG
from tqdm import tqdm

from app.caches import DeputyDevCache
from app.constants.constants import BATCH_SIZE
from app.modules.chunking.chunk_info import ChunkInfo
from app.modules.tiktoken import TikToken
from app.utils import hash_sha256

config = CONFIG.config
client = OpenAI(api_key=config.get("OPENAI_KEY"))

tiktoken_client = TikToken()


async def embed_text_array(texts: Tuple[str]) -> List[np.ndarray]:
    """
    Embeds a list of texts using OpenAI's embedding model.

    Args:
        texts (tuple[str]): A tuple of texts to embed.

    Returns:
        list[np.ndarray]: List of embeddings for each text.
    """
    embeddings = []
    texts = [text if text else " " for text in texts]
    batches = [texts[i : i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
    workers = min(max(1, multiprocessing.cpu_count() // 4), 1)
    if workers > 1:
        with multiprocessing.Pool(processes=workers) as pool:
            embeddings = list(
                tqdm(
                    pool.imap(await get_embeddings, batches),
                    total=len(batches),
                    desc="openai embedding",
                )
            )
    else:
        embeddings = [await get_embeddings(batch) for batch in tqdm(batches, desc="openai embedding")]
    return embeddings


def normalize_l2(x: np.ndarray) -> np.ndarray:
    """
    Normalize vectors using L2 normalization.

    Args:
        x (np.ndarray): Input vectors.

    Returns:
        np.ndarray: Normalized vectors.
    """
    x = np.array(x)
    if x.ndim == 1:
        norm = np.linalg.norm(x)
        if norm == 0:
            return x
        return x / norm
    else:
        norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
        return np.where(norm == 0, x, x / norm)


def call_embedding(batch: List[str]) -> np.ndarray:
    """
    Calls OpenAI's embedding model to embed a batch of texts.

    Args:
        batch (list[str]): Batch of texts to embed.

    Returns:
        np.ndarray: Embedded vectors.
    """
    response = client.embeddings.create(input=batch, model="text-embedding-3-small", encoding_format="float")
    cut_dim = np.array([data.embedding for data in response.data])
    normalized_dim = normalize_l2(cut_dim)
    # save results to redis
    return normalized_dim


async def get_embeddings(batch: Tuple[str]) -> np.ndarray:
    """
    Gets embeddings for a batch of texts.

    Args:
        batch (tuple[str]): Batch of texts.

    Returns:
        np.ndarray: Embedded vectors.
    """
    embeddings: List[np.ndarray] = [None] * len(batch)
    cache_keys = [hash_sha256(text) for text in batch]
    try:
        for i, cache_value in enumerate(await DeputyDevCache.mget(cache_keys)):
            if cache_value:
                embeddings[i] = np.array(json.loads(cache_value))
    except Exception as e:
        logger.exception(e)

    batch = [text for i, text in enumerate(batch) if embeddings[i] is None]
    if len(batch) == 0:
        embeddings = np.array(embeddings)
        return embeddings

    try:
        new_embeddings = call_embedding(batch)
    except requests.exceptions.Timeout as e:
        logger.exception(f"Timeout error occurred while embedding: {e}")
    except Exception as e:
        logger.exception(e)
        if any(tiktoken_client.count(text) > 8192 for text in batch):
            logger.warning(
                f"Token count exceeded for batch: {max([tiktoken_client.count(text) for text in batch])} "
                f"truncating down to 8192 tokens."
            )
            batch = [tiktoken_client.truncate_string(text) for text in batch]
            new_embeddings = call_embedding(batch)
        else:
            raise e

    indices = [i for i, emb in enumerate(embeddings) if emb is None]
    assert len(indices) == len(new_embeddings)
    for i, index in enumerate(indices):
        embeddings[index] = new_embeddings[i]

    try:
        await DeputyDevCache.mset(
            {cache_key: json.dumps(embedding.tolist()) for cache_key, embedding in zip(cache_keys, embeddings)}
        )
        embeddings = np.array(embeddings)
    except Exception:
        logger.error("Failed to store embeddings in cache, returning without storing")
    return embeddings


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


async def get_query_texts_similarity(query: str, texts: List[str]) -> List[float]:
    """
    Computes the cosine similarity between a query and a list of texts.

    Args:
        query (str): The query text.
        texts (list[str]): List of texts to compare against the query.

    Returns:
        list[float]: List of cosine similarity scores.
    """
    if not texts:
        return []
    embeddings = await embed_text_array(texts)
    embeddings = np.concatenate(embeddings)
    query_embedding = np.array(call_embedding([query]))
    similarity = cosine_similarity(query_embedding, embeddings)
    similarity = similarity.tolist()
    return similarity


async def compute_vector_search_scores(query: str, chunks: List[ChunkInfo]) -> dict:
    """
    Computes vector search scores for a query and a list of ChunkInfo objects.

    Args:
        query (str): The query string.
        chunks (list[ChunkInfo]): List of ChunkInfo objects representing text chunks.

    Returns:
        dict: Dictionary mapping chunk denotations to similarity scores.
    """
    chunk_str_to_contents = {
        chunk.denotation: chunk.get_chunk_content(add_ellipsis=False, add_lines=False) for chunk in chunks
    }
    chunk_contents_array = list(chunk_str_to_contents.values())
    query_snippet_similarities = await get_query_texts_similarity(query, chunk_contents_array)
    chunk_denotations = [chunk.denotation for chunk in chunks]
    chunk_denotation_to_scores = {chunk_denotations[i]: score for i, score in enumerate(query_snippet_similarities)}
    return chunk_denotation_to_scores
