from typing import List, Optional, Tuple

import numpy as np
from prompt_toolkit.shortcuts.progress_bar import ProgressBar

from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.main.blueprints.one_dev_cli.app.clients.one_dev import OneDevClient


class OneDevEmbeddingManager(BaseEmbeddingManager):
    def __init__(self, auth_token: str, progressbar: Optional[ProgressBar] = None):
        self.auth_token = auth_token
        self.progressbar = progressbar

    async def embed_text_array(self, texts: List[str], store_embeddings: bool = True) -> Tuple[List[np.ndarray], int]:
        oen_dev_client = OneDevClient()

        # create batches of 10 texts
        batches: List[List[str]] = []
        batch_size = 10

        for i in range(0, len(texts), batch_size):
            batches.append(texts[i : i + batch_size])

        embeddings: List[List[float]] = []
        tokens_used: int = 0

        iterable_batch = (
            self.progressbar(batches, label="Setting up DeputyDev's intelligence", total=len(batches))
            if self.progressbar
            else batches
        )

        for batch in iterable_batch:
            embedding_result = await oen_dev_client.create_embedding(
                payload={"texts": batch, "store_embeddings": store_embeddings},
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.auth_token}"},
            )
            embeddings.extend(embedding_result["embeddings"])
            tokens_used += embedding_result["tokens_used"]

        return np.array(embeddings), tokens_used
