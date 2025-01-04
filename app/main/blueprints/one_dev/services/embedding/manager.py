from typing import List

from app.backend_common.services.embedding.openai_embedding_manager import (
    OpenAIEmbeddingManager,
)
from app.main.blueprints.one_dev.services.embedding.dataclasses.main import (
    OneDevEmbeddingPayload,
)


class OneDevEmbeddingManager:
    @classmethod
    async def create_embeddings(cls, payload: OneDevEmbeddingPayload) -> List[List[float]]:
        embeddings, tokens_used = await OpenAIEmbeddingManager.embed_text_array(
            texts=payload.texts, store_embeddings=payload.store_embeddings
        )
        return {"embeddings": [embedding.tolist() for embedding in embeddings], "tokens_used": tokens_used}
