from datetime import datetime

from pydantic import BaseModel


class ChatAttachmentsData(BaseModel):
    file_name: str
    file_type: str
    s3_key: str


class ChatAttachmentsDTO(ChatAttachmentsData):
    id: int
    created_at: datetime
    updated_at: datetime
