import json
from typing import List, Tuple

import httpx
import numpy as np
import requests
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage
from sanic.log import logger
from torpedo import CONFIG

from app.common.caches import DeputyDevCache
from app.common.services.openai.base import BaseClient
from app.common.utils.app_utils import hash_sha256
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken

openai_key = CONFIG.config.get("OPENAI_KEY")


class OpenAIClient(BaseClient):
    def __init__(self):
        self.__client = AsyncOpenAI(
            api_key=openai_key,
            timeout=600,
            http_client=httpx.AsyncClient(
                timeout=60,
                limits=httpx.Limits(
                    max_connections=1000,
                    max_keepalive_connections=100,
                    keepalive_expiry=20,
                ),
            ),
        )
        self.tiktoken_client = TikToken()

    async def __call_embedding(self, batch: List[str]) -> np.ndarray:
        """
        Calls OpenAI's embedding model to embed a batch of texts.

        Args:
            batch (list[str]): Batch of texts to embed.

        Returns:
            np.ndarray: Embedded vectors.
        """
        response = await self.__client.embeddings.create(
            input=batch, model="text-embedding-3-small", encoding_format="float"
        )
        cut_dim = np.array([data.embedding for data in response.data])
        normalized_dim = self.normalize_l2(cut_dim)
        # save results to redis
        return normalized_dim

    # We can make the get_embeddings function more generic as redis layer should not be part of openai class
    async def get_embeddings(self, batch: Tuple[str]) -> np.ndarray:
        """
        Gets embeddings for a batch of texts.

        Args:
            batch (tuple[str]): Batch of texts.

        Returns:
            np.ndarray: Embedded vectors.
        """
        if len(batch) == 1:
            embeddings = await self.__call_embedding(batch)
            return np.array(embeddings)
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
            new_embeddings = await self.__call_embedding(batch)
        except requests.exceptions.Timeout as e:
            logger.exception(f"Timeout error occurred while embedding: {e}")
        except Exception as e:
            logger.exception(e)
            if any(self.tiktoken_client.count(text) > 8192 for text in batch):
                logger.warning(
                    f"Token count exceeded for batch: {max([self.tiktoken_client.count(text) for text in batch])} "
                    f"truncating down to 8192 tokens."
                )
                batch = [self.tiktoken_client.truncate_string(text) for text in batch]
                new_embeddings = await self.__call_embedding(batch)
            else:
                raise e

        indices = [i for i, emb in enumerate(embeddings) if emb is None]
        assert len(indices) == len(new_embeddings)
        for i, index in enumerate(indices):
            embeddings[index] = new_embeddings[i]

        try:
            await DeputyDevCache.mset_with_expire(
                {cache_key: json.dumps(embedding.tolist()) for cache_key, embedding in zip(cache_keys, embeddings)}
            )
            embeddings = np.array(embeddings)
        except Exception:
            logger.error("Failed to store embeddings in cache, returning without storing")
        return embeddings

    async def get_openai_response(
        self, conversation_messages: list, model: str, response_type: str = "json_object"
    ) -> ChatCompletionMessage:
        """
        Retrieve a response from the OpenAI Chat API.
        Args:
            conversation_messages (list): A list of conversation messages, including both system and user messages.
            model (str): The name or identifier of the GPT model to use for the completion.
        Returns:
            ChatCompletionMessage: The completed message returned by the OpenAI Chat API.
        Raises:
            OpenAIException: If there is an error while communicating with the OpenAI API or processing the response.
        """
        completion = await self.__client.chat.completions.create(
            model=model,
            response_format={"type": response_type},
            messages=conversation_messages,
            temperature=0.5,
        )
        return completion.choices[0].message
