import base64
import mimetypes
from typing import Dict, Any, Optional

from app.backend_common.service_clients.aws_s3.aws_s3_service_client import AWSS3ServiceClient
from deputydev_core.utils.app_logger import AppLogger


class FileProcessor:

    async def process_file(self, s3_key: str) -> Dict[str, Any]:
        try:
            file_data = await AWSS3ServiceClient().get_file(s3_key)
            file_type = await self.get_file_mimetype(s3_key)

            if file_type and file_type.startswith("image/"):
                file_content_base64 = base64.b64encode(file_data).decode("utf-8")
                return {"type": file_type, "content": file_data, "content_base64": file_content_base64}
            else:
                raise ValueError("Unsupported file type")
        except Exception as ex:
            AppLogger.log_error(f"Error processing file from S3: {ex}")
            raise

    async def get_file_mimetype(self, s3_key: str) -> Optional[str]:
        file_type, _ = mimetypes.guess_type(s3_key)
        return file_type
