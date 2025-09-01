import asyncio
from typing import List, Tuple

import numpy as np
from deputydev_core.services.embedding.base_embedding_manager import (
    BaseEmbeddingManager,
)
from deputydev_core.services.tiktoken.tiktoken import TikToken
from deputydev_core.utils.app_logger import AppLogger
from numpy.typing import NDArray
from sanic.log import logger

from app.backend_common.services.openai.openai_llm_service import OpenAILLMService
from app.backend_common.utils.sanic_wrapper import CONFIG

config = CONFIG.config


class OpenAIEmbeddingManager(BaseEmbeddingManager):
    @classmethod
    def create_optimized_batches(cls, texts: List[str], max_tokens: int, model: str) -> List[List[str]]:
        tiktoken_client = TikToken()
        batches = []
        current_batch = []
        currrent_batch_token_count = 0

        for text in texts:
            text_token_count = tiktoken_client.count(text, model=model)

            if text_token_count > max_tokens:  # Single text exceeds max tokens
                truncated_text = tiktoken_client.truncate_string(text=text, max_tokens=max_tokens, model=model)
                batches.append([truncated_text])
                logger.warn(f"Text with token count {text_token_count} exceeds the max token limit of {max_tokens}.")
                continue

            if currrent_batch_token_count + text_token_count > max_tokens:
                batches.append(current_batch)
                current_batch = [text]
                currrent_batch_token_count = text_token_count
            else:
                current_batch.append(text)
                currrent_batch_token_count += text_token_count

        if current_batch:
            batches.append(current_batch)

        return batches

    @classmethod
    async def embed_text_array(cls, texts: List[str], store_embeddings: bool = True) -> Tuple[NDArray[np.float64], int]:  # noqa: C901
        """
        Embeds a list of texts using OpenAI's embedding model.

        Args:
            texts (tuple[str]): A tuple of texts to embed.
            store_embeddings (bool): If true we will store embeddings in Redis

        Returns:
            list[np.ndarray]: List of embeddings for each text.
        """
        embeddings = []
        input_tokens = 0
        texts = [text if text else " " for text in texts]

        AppLogger.log_debug(f"Embedding {len(texts)} texts using OpenAI's embedding model")
        batches = cls.create_optimized_batches(
            texts, max_tokens=config["EMBEDDING"]["TOKEN_LIMIT"], model=config["EMBEDDING"]["MODEL"]
        )
        AppLogger.log_debug(f"Created Optimized {len(batches)} batches for embedding using {len(texts)} texts")

        max_parallel_tasks = 30
        parallel_batches = []
        exponential_backoff = 0.2
        for batch in batches:
            if not batch:
                continue
            if len(parallel_batches) >= max_parallel_tasks:
                AppLogger.log_debug(f"Starting embedding for {len(parallel_batches)} in parallel")
                parallel_tasks = [
                    OpenAILLMService().get_embeddings(batch, store_embeddings) for batch in parallel_batches
                ]
                AppLogger.log_debug(f"Starting embedding for {len(parallel_batches)} in parallel")
                batch_result = await asyncio.gather(*parallel_tasks, return_exceptions=True)
                AppLogger.log_debug(f"Batch of {len(parallel_batches)} completed for embedding")
                failed_batches = []
                for _data, data_batch in zip(batch_result, parallel_batches):
                    if isinstance(_data, Exception):
                        AppLogger.log_debug(_data)
                        AppLogger.log_debug(f"Failed embedding batch: {_data}")
                        failed_batches.append(data_batch)
                    else:
                        embeddings.extend(_data[0])
                        input_tokens += _data[1]

                parallel_batches = []
                if failed_batches:
                    await asyncio.sleep(exponential_backoff)
                    exponential_backoff *= 2
                    parallel_batches += failed_batches
                # store current batch
                parallel_batches += [batch]
            else:
                parallel_batches.append(batch)

        while len(parallel_batches) > 0:
            parallel_tasks = [OpenAILLMService().get_embeddings(batch, store_embeddings) for batch in parallel_batches]
            batch_result = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            AppLogger.log_debug(f"Batch of {len(parallel_batches)} completed for embedding")
            failed_batches = []
            for _data, data_batch in zip(batch_result, parallel_batches):
                if isinstance(_data, Exception):
                    AppLogger.log_debug(f"Failed embedding batch: {_data}")
                    failed_batches.append(data_batch)
                else:
                    embeddings.extend(_data[0])
                    input_tokens += _data[1]

            parallel_batches = []
            if failed_batches:
                await asyncio.sleep(exponential_backoff)
                exponential_backoff *= 2
                parallel_batches += failed_batches

        return embeddings, input_tokens
