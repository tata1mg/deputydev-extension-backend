from typing import Any, Dict

from pydantic import BaseModel


class PresignedDownloadUrls(BaseModel):
    upload_url: Dict[str, Any]
    download_url: str
    attachment_id: int
