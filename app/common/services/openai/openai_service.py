import json
from typing import List, Tuple

import numpy as np
import requests
from sanic.log import logger
from torpedo import CONFIG

from app.common.caches import DeputyDevCache
from app.common.service_clients.openai.openai import OpenAIServiceClient
from app.common.services.openai.base_client import BaseClient
from app.common.utils.app_utils import hash_sha256
from app.main.blueprints.deputy_dev.services.context_var import identifier
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)

openai_key = CONFIG.config.get("OPENAI_KEY")


class OpenAIManager(BaseClient):
    def __init__(self):
        self.tiktoken_client = TikToken()

    async def __call_embedding(self, batch: List[str]) -> np.ndarray:
        """
        Calls OpenAI's embedding model to embed a batch of texts.

        Args:
            batch (list[str]): Batch of texts to embed.

        Returns:
            np.ndarray: Embedded vectors.
        """
        response = await OpenAIServiceClient().create_embedding(input=batch)
        cut_dim = np.array([data.embedding for data in response.data])
        normalized_dim = self.normalize_l2(cut_dim)
        # save results to redis
        return normalized_dim, response.usage.prompt_tokens

    def get_cache_prefix(self):
        repo_name = identifier.get(None)
        team_id = get_context_value("team_id")
        if team_id == 1:
            # TODO added this check for backward compatibility and needs to be removed
            prefix_key = repo_name
        else:
            prefix_key = f"{team_id}:{repo_name}"
        return prefix_key

    # We can make the get_embeddings function more generic as redis layer should not be part of openai class
    async def get_embeddings(self, batch: Tuple[str]) -> np.ndarray:
        """
        Gets embeddings for a batch of texts.

        Args:
            batch (tuple[str]): Batch of texts.

        Returns:
            np.ndarray: Embedded vectors.
        """
        input_tokens = None
        # "identifier" will try to get the context value which was set, if not found, it will return None
        key = self.get_cache_prefix()
        if len(batch) == 1:
            embeddings, input_tokens = await self.__call_embedding(batch)
            return np.array(embeddings), input_tokens
        embeddings: List[np.ndarray] = [None] * len(batch)
        cache_keys = [f"{key}:{hash_sha256(text)}" if key else hash_sha256(text) for text in batch]
        try:
            for i, cache_value in enumerate(await DeputyDevCache.mget(cache_keys)):
                if cache_value:
                    embeddings[i] = np.array(json.loads(cache_value))
        except Exception as e:
            logger.exception(e)

        batch = [text for i, text in enumerate(batch) if embeddings[i] is None]
        if len(batch) == 0:
            embeddings = np.array(embeddings)
            return embeddings, input_tokens

        try:
            new_embeddings, input_tokens = await self.__call_embedding(batch)
        except requests.exceptions.Timeout as e:
            raise e
        except Exception as e:
            if any(self.tiktoken_client.count(text) > 8192 for text in batch):
                logger.warning(
                    f"Token count exceeded for batch: {max([self.tiktoken_client.count(text) for text in batch])} "
                    f"truncating down to 8192 tokens."
                )
                batch = [self.tiktoken_client.truncate_string(text) for text in batch]
                new_embeddings, input_tokens = await self.__call_embedding(batch)
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
        return embeddings, input_tokens
