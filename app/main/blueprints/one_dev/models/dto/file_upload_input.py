from typing import Literal, Annotated
from pydantic import BaseModel, Field


class FileUploadPostInput(BaseModel):
    file_name: str
    file_size: Annotated[int, Field(ge=1, le=5 * 1024 * 1024)]
    file_type: Literal["image/jpeg", "image/jpg", "image/png", "image/webp", "application/json"]
    folder: Literal["image", "payload"] = "image"


class FileUploadGetInput(BaseModel):
    attachment_id: int


class FileDeleteInput(BaseModel):
    attachment_id: int
