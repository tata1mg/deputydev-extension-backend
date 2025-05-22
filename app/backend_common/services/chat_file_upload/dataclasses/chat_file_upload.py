from pydantic import BaseModel


class PresignedDownloadUrls(BaseModel):
    upload_url: str
    download_url: str
    s3_key: str
