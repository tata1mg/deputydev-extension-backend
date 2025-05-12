from typing import List

from pydantic import BaseModel


class OneDevEmbeddingPayload(BaseModel):
    texts: List[str]
    store_embeddings: bool
