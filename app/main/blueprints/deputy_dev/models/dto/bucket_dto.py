from typing import Optional

from pydantic import BaseModel


class BucketDTO(BaseModel):
    id: Optional[int] = None
    name: str
    weight: int
    bucket_type: str
    status: str
    description: Optional[str] = ""
    is_llm_suggested: Optional[bool] = False

    class Config:
        orm_mode = True
