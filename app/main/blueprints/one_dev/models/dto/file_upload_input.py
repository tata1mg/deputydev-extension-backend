from typing import Literal
from pydantic import BaseModel, conint


class FileUploadPostInput(BaseModel):
    file_name: str
    file_size: conint(ge=1, le=5 * 1024 * 1024 * 1024)
    file_type: Literal["image/jpeg", "image/jpg", "image/png", "image/webp"]


class FileUploadGetInput(BaseModel):
    s3_key: str
