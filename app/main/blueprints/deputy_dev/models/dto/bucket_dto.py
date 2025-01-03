from typing import Optional

from pydantic import BaseModel, ConfigDict


class BucketDTO(BaseModel):
    id: Optional[int] = None
    name: str
    weight: int
    bucket_type: str
    status: str
    description: Optional[str] = ""
    is_llm_suggested: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)
