from typing import List, Optional

from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


class OneDevEmbeddingPayload(BaseModel):
    texts: List[str]
    store_embeddings: bool
    auth_data: AuthData
