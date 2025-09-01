import json
from typing import List, Optional

import numpy as np
import requests
from deputydev_core.services.tiktoken import TikToken
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.context_vars import get_context_value
from sanic.log import logger

from app.backend_common.caches.common import CommonCache
from app.backend_common.constants.error_messages import ErrorMessages
from app.backend_common.service_clients.openai.openai import OpenAIServiceClient
from app.backend_common.services.openai.base_client import BaseClient
from app.backend_common.services.workspace.context_var import identifier
from app.backend_common.utils.app_utils import hash_sha256
from app.backend_common.utils.sanic_wrapper import CONFIG

openai_key = CONFIG.config.get("OPENAI_KEY")
EMBEDDING_MODEL = CONFIG.config.get("EMBEDDING").get("MODEL")
EMBEDDING_TOKEN_LIMIT = ConfigManager.configs["EMBEDDING"]["TOKEN_LIMIT"]


class OpenAIManager(BaseClient):
    def __init__(self) -> None:
        self.tiktoken_client = TikToken()

    async def __call_embedding(self, batch: List[str]) -> np.ndarray:
        """
        Calls OpenAI's embedding model to embed a batch of texts.

        Args:
            batch (list[str]): Batch of texts to embed.

        Returns:
            np.ndarray: Embedded vectors.
        """
        response = await OpenAIServiceClient().create_embedding(
            input=batch, model=EMBEDDING_MODEL, encoding_format="float"
        )

        cut_dim = np.array([data.embedding for data in response.data])
        normalized_dim = self.normalize_l2(cut_dim)
        # save results to redis

        if len(batch) == 1:
            logger.info(f"Input text: {batch[0]}")
            logger.info(f"Embedding: {normalized_dim}")
        return normalized_dim, response.usage.prompt_tokens

    def get_cache_prefix(self) -> str:
        repo_name: Optional[str] = identifier.get(None)
        team_id = get_context_value("team_id")
        if team_id == 1:
            # TODO added this check for backward compatibility and needs to be removed
            prefix_key = repo_name
        else:
            prefix_key = f"{team_id}:{repo_name}"
        return prefix_key

    async def create_embeddings(self, batch: List[str]) -> Optional[List[float]]:
        """
        Create embeddings for a batch of text strings.

        Args:
            batch (Tuple[str]): A tuple of text strings to embed.

        Returns:
            Optional[List[float]]: A list of embeddings if successful, None if there was a timeout.
        """
        new_embeddings = None
        try:
            new_embeddings, input_tokens = await self.__call_embedding(batch)
        except requests.exceptions.Timeout as e:
            AppLogger.log_error(f"Timeout error occurred while embedding: {e}")
        except Exception as e:
            AppLogger.log_warn(e)
            if any(self.tiktoken_client.count(text) > EMBEDDING_TOKEN_LIMIT for text in batch):
                new_batch = []
                for text in batch:
                    if self.tiktoken_client.count(text) > EMBEDDING_TOKEN_LIMIT:
                        AppLogger.log_warn(
                            ErrorMessages.TOKEN_COUNT_EXCEED_WARNING.value.format(
                                count=self.tiktoken_client.count(text),
                                token_limit=EMBEDDING_TOKEN_LIMIT,
                            )
                        )
                    new_batch.append(self.tiktoken_client.truncate_string(text))
                new_embeddings, input_tokens = await self.__call_embedding(new_batch)
            else:
                raise e
        return new_embeddings, input_tokens

    # We can make the get_embeddings function more generic as redis layer should not be part of openai class
    async def get_embeddings(self, batch: List[str], store_embeddings: bool = True) -> np.ndarray:
        """
        Gets embeddings for a batch of texts.

        Args:
            batch (tuple[str]): Batch of texts.
            store_embeddings (bool): If true we will store embeddings in Redis

        Returns:
            np.ndarray: Embedded vectors.
        """
        input_tokens = 0
        # "identifier" will try to get the context value which was set, if not found, it will return None
        key: Optional[str] = self.get_cache_prefix()
        if not store_embeddings:
            batch = self.tiktoken_client.split_text_by_tokens(batch[0])
            embeddings, input_tokens = await self.create_embeddings(batch=batch)

            return np.array(embeddings), input_tokens
        embeddings: List[np.ndarray] = [None] * len(batch)
        cache_keys = [f"{key}:{hash_sha256(text)}" if key else hash_sha256(text) for text in batch]
        try:
            for i, cache_value in enumerate(await CommonCache.mget(cache_keys)):
                if cache_value:
                    embeddings[i] = np.array(json.loads(cache_value))
        except Exception as e:  # noqa: BLE001
            logger.exception(e)

        batch = [text for i, text in enumerate(batch) if embeddings[i] is None]

        if len(batch) == 0:  # when we get all embeddings from cache
            embeddings = np.array(embeddings)
            return embeddings, input_tokens

        new_embeddings, input_tokens = await self.create_embeddings(batch=batch)

        indices = [i for i, emb in enumerate(embeddings) if emb is None]
        assert len(indices) == len(new_embeddings)
        for i, index in enumerate(indices):
            embeddings[index] = new_embeddings[i]

        try:
            for i in range(0, len(cache_keys), 100):
                batch_keys = cache_keys[i : i + 100]
                batch_embeddings = embeddings[i : i + 100]

                # Store the current batch in Redis
                await CommonCache.mset_with_expire(
                    {
                        cache_key: json.dumps(embedding.tolist())
                        for cache_key, embedding in zip(batch_keys, batch_embeddings)
                    }
                )
            embeddings = np.array(embeddings)
        except Exception:  # noqa: BLE001
            logger.error("Failed to store embeddings in cache, returning without storing")
        return embeddings, input_tokens
