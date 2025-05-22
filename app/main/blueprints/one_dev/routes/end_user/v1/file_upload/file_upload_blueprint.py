from sanic import Blueprint, response
from torpedo import Request, send_response
from sanic.request import File
import uuid
import io
import tempfile
import aiofiles
import urllib.parse
from app.main.blueprints.one_dev.models.dto.file_upload_input import FileUploadPostInput, FileUploadGetInput
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.session import ensure_session_id
from app.backend_common.service_clients.aws_s3.aws_s3_service_client import AWSS3ServiceClient


file_upload_v1_bp = Blueprint("file_upload_v1_bp", url_prefix="/file-upload")

    
@file_upload_v1_bp.route("/get-presigned-post-url", methods=["POST"])
async def get_presigned_post_url(_request: Request, **kwargs):

    payload = _request.custom_json()
    payload = FileUploadPostInput(**payload)

    file_extension = payload.file_name.split(".")[-1] if payload.file_name else None

    s3_key = f"{uuid.uuid4()}.{file_extension}"

    try:
        presigned_url = await AWSS3ServiceClient().create_presigned_post_url(s3_key, payload.file_type)
    except Exception as e:
        raise Exception(e)
    return send_response(presigned_url)



@file_upload_v1_bp.route("/get-presigned-get-url", methods=["POST"])
async def get_presigned_get_url(_request: Request, **kwargs):

    payload = _request.custom_json()
    payload = FileUploadGetInput(**payload)

    try:
        s3_key = payload.file_name
        presigned_url = await AWSS3ServiceClient().create_presigned_get_url(
            object_name=s3_key,
            expiration=600
        )
    except Exception as e:
        raise Exception(e)

    return send_response(presigned_url)

