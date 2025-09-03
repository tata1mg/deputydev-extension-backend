from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.main.blueprints.one_dev.services.embedding.dataclasses.main import (
    OneDevEmbeddingPayload,
)
from app.main.blueprints.one_dev.services.embedding.manager import (
    OneDevEmbeddingManager,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

code_gen_v1_bp = Blueprint("code_gen_v1_bp", url_prefix="/code-gen")


@code_gen_v1_bp.route("/get-job-status", methods=["GET"])
@validate_client_version
@authenticate
async def get_job_status(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | JSONResponse:
    payload = {key: var for key, var in _request.query_args}
    job = await JobService.db_get(filters={"id": int(payload.get("job_id"))}, fetch_one=True)
    if not job:
        return send_response({"status": "JOB_NOT_FOUND"})
    response = {
        "status": job.status,
        "response": job.final_output,
    }
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/create-embedding", methods=["POST"])
@validate_client_version
# @authenticate
async def get_embeddings(_request: Request, client_data: ClientData, **kwargs: Any) -> ResponseDict | JSONResponse:
    payload = _request.custom_json()
    response = await OneDevEmbeddingManager.create_embeddings(payload=OneDevEmbeddingPayload(**payload))
    return send_response(response, headers=kwargs.get("response_headers"))
