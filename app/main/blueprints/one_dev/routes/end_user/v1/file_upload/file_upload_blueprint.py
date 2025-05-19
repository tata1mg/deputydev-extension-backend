from sanic import Blueprint, response
from torpedo import Request, send_response
from sanic.request import File
import uuid
import io
import tempfile
import aiofiles
import urllib.parse
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.session import ensure_session_id
from app.backend_common.service_clients.aws_s3.aws_s3_service_client import AWSS3ServiceClient


file_upload_v1_bp = Blueprint("file_upload_v1_bp", url_prefix="/file-upload")


BUCKET_NAME = "deputydev"
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB


    
@file_upload_v1_bp.route("/get-presigned-post-url", methods=["POST"])
async def get_presigned_post_url(_request: Request, **kwargs):


    payload = _request.custom_json()

    file_name = payload.get("file_name")
    file_size = payload.get("file_size")
    file_type = payload.get("file_type")

    file_extension = file_name.split(".")[-1] if file_name else None

    if not file_name or not file_size or not file_type:
        return response.json({"error": "file_name, file_size, and file_type are required"}, status=400)
    
    if file_size > 5 * 1024 * 1024:  # 5 MB
        return response.json({"error": "File size exceeds the limit of 5 MB"}, status=400)
    
    if file_type not in ["image/jpeg", "image/jpg", "image/png"]:
        return response.json({"error": "Invalid file type. Allowed: jpeg, jpg, png"}, status=400)

    s3_key = f"{uuid.uuid4()}.{file_extension}"

    try:
        presigned_url = await AWSS3ServiceClient().create_presigned_post_url(s3_key, file_type)
    except Exception as e:
        raise Exception(e)
    return send_response(presigned_url)



@file_upload_v1_bp.route("/get-presigned-get-url", methods=["POST"])
async def get_presigned_get_url(_request: Request, **kwargs):

    if not _request.json:
        return response.json({"error": "Request body is required"}, status=400)

    file_name = _request.json.get("file_name")

    if not file_name:
        return response.json({"error": "file_name is required"}, status=400)

    try:
        s3_key = file_name

        presigned_url = await AWSS3ServiceClient().create_presigned_get_url(
            object_name=s3_key,
            expiration=600 # 10 minutes
        )
    except Exception as e:
        raise Exception(e)

    return send_response(presigned_url)

