import time
from typing import List, Tuple

import numpy as np

from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.tiktoken.tiktoken import TikToken
from app.common.utils.app_logger import AppLogger
from app.main.blueprints.deputydev_cli.app.clients.one_dev import OneDevClient


class OneDevEmbeddingManager(BaseEmbeddingManager):
    def __init__(self, auth_token: str):
        self.auth_token = auth_token

    @classmethod
    def create_optimized_batches(
        self, texts: List[str], max_tokens_per_text: int, max_tokens_per_batch: int, model: str
    ) -> List[List[str]]:
        tiktoken_client = TikToken()
        batches: List[List[str]] = []
        current_batch = []
        currrent_batch_token_count = 0

        for text in texts:
            text_token_count = tiktoken_client.count(text, model=model)

            if text_token_count > max_tokens_per_text:  # Single text exceeds max tokens
                batches.append([text])
                AppLogger.log_warn(
                    f"Text with token count {text_token_count} exceeds the max token limit of {max_tokens_per_text}."
                )
                continue

            if currrent_batch_token_count + text_token_count > max_tokens_per_batch:
                batches.append(current_batch)
                current_batch = [text]
                currrent_batch_token_count = text_token_count
            else:
                current_batch.append(text)
                currrent_batch_token_count += text_token_count

        if current_batch:
            batches.append(current_batch)

        return batches

    async def embed_text_array(self, texts: List[str], store_embeddings: bool = True) -> Tuple[List[np.ndarray], int]:
        oen_dev_client = OneDevClient()
        embeddings: List[List[float]] = []
        tokens_used: int = 0

        iterable_batch = self.create_optimized_batches(
            texts, max_tokens_per_text=4096, max_tokens_per_batch=2048, model="text-embedding-3-small"
        )

        for batch in iterable_batch:
            time_start = time.perf_counter()
            embedding_result = await oen_dev_client.create_embedding(
                payload={"texts": batch, "store_embeddings": store_embeddings},
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.auth_token}"},
            )
            AppLogger.log_debug(f"Time taken for embedding batch via API: {time.perf_counter() - time_start}")
            embeddings.extend(embedding_result["embeddings"])
            tokens_used += embedding_result["tokens_used"]

        return np.array(embeddings), tokens_used
