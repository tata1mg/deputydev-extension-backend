from sanic import Blueprint
from torpedo import Request, send_response
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.main.blueprints.one_dev.models.dto.file_upload_input import FileUploadPostInput
from typing import Any
from torpedo.exceptions import HTTPRequestException

from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import validate_client_version
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


file_upload_v1_bp = Blueprint("file_upload_v1_bp", url_prefix="/file-upload")


@file_upload_v1_bp.route("/get-presigned-post-url", methods=["POST"])
@validate_client_version
@authenticate
async def get_presigned_post_url(_request: Request, auth_data: AuthData, **kwargs: Any):
    payload = FileUploadPostInput(**_request.custom_json())
    print(f"Received payload: {payload}")
    try:
        presigned_urls = await ChatFileUpload.get_presigned_urls_for_upload(
            file_name=payload.file_name,
            file_type=payload.file_type,
        )
        return send_response(presigned_urls.model_dump(mode="json"))
    except Exception as _ex:
        raise HTTPRequestException(
            f"Error generating presigned URL: {_ex}",
        )
