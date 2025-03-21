from typing import List

from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from typing import Optional


class OneDevEmbeddingPayload(BaseModel):
    texts: List[str]
    store_embeddings: bool
    auth_data: AuthData
