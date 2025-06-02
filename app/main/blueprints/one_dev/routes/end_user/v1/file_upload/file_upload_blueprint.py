from sanic import Blueprint
from torpedo import Request, send_response
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.main.blueprints.one_dev.models.dto.file_upload_input import FileUploadPostInput, FileUploadGetInput, FileDeleteInput
from typing import Any
from torpedo.exceptions import HTTPRequestException

from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import validate_client_version
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository


file_upload_v1_bp = Blueprint("file_upload_v1_bp", url_prefix="/file-upload")


@file_upload_v1_bp.route("/get-presigned-post-url", methods=["POST"])
@validate_client_version
@authenticate
async def get_presigned_post_url(_request: Request, auth_data: AuthData, **kwargs: Any):
    payload = FileUploadPostInput(**_request.custom_json())
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


@file_upload_v1_bp.route("/get-presigned-get-url", methods=["POST"])
@validate_client_version
@authenticate
async def get_presigned_get_url(_request: Request, auth_data: AuthData, **kwargs: Any):
    payload = FileUploadGetInput(**_request.custom_json())
    
    try:
        attachment = await ChatAttachmentsRepository.get_attachment_by_id(
            attachment_id=payload.attachment_id,
        )
        if not attachment:
            raise HTTPRequestException(f"Attachment with ID {payload.attachment_id} not found.")
        presigned_get_url = await ChatFileUpload.get_presigned_url_for_fetch_by_s3_key(
            s3_key=attachment.s3_key
        )
        return send_response({"download_url": presigned_get_url, "file_name": attachment.file_name})
    except Exception as _ex:
        raise HTTPRequestException(
            f"Error generating presigned URL: {_ex}",
        )
    

@file_upload_v1_bp.route("/delete-file", methods=["POST"])
@validate_client_version
@authenticate
async def delete_attachment(_request: Request, auth_data: AuthData, **kwargs: Any):
    payload = FileDeleteInput(**_request.custom_json())
    
    try:
        await ChatAttachmentsRepository.update_attachment_status(
            attachment_id=payload.attachment_id,
            status="deleted",
        )
        return send_response({"message": "Attachment deleted successfully."})
    except Exception as _ex:
        raise HTTPRequestException(
            f"Error deleting attachment: {_ex}",
        )