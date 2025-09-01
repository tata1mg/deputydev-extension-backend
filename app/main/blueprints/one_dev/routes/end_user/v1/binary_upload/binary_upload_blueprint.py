from typing import Any

from deputydev_core.utils.config_manager import ConfigManager
from sanic import Blueprint

from app.backend_common.services.binary_file_upload.binary_file_upload import BinaryFileUpload
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import HTTPRequestException

binary_upload_v1_bp = Blueprint("binary_upload_v1_bp", url_prefix="/binary-upload")


@binary_upload_v1_bp.route("/get-presigned-url", methods=["POST"])
async def get_presigned_url(_request: Request, **kwargs: Any) -> dict[str, Any]:
    BINARY_UPLOAD_AUTH_KEY = ConfigManager.configs["BINARY_UPLOAD"]["AUTH_KEY"]  # noqa: N806
    client_key = _request.headers.get("authorization")
    if client_key != BINARY_UPLOAD_AUTH_KEY:
        raise HTTPRequestException("Invalid API key", status_code=401)
    try:
        payload = _request.custom_json()
        s3_key = payload["s3_key"]
        if not s3_key:
            raise HTTPRequestException("s3_key is required")
        presigned_url_for_binary_upload = await BinaryFileUpload.get_presigned_urls_for_upload(s3_key)
        return send_response({"presigned_url": presigned_url_for_binary_upload})
    except Exception as _ex:  # noqa: BLE001
        raise HTTPRequestException(
            f"Error generating presigned URL: {_ex}",
        )
