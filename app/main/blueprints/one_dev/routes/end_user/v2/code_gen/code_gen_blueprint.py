import json
from typing import Any

from sanic import Blueprint
from torpedo import Request, send_response

from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
    QuerySolverInput,
)
from app.main.blueprints.one_dev.services.query_solver.inline_editor import (
    InlineEditGenerator,
)
from app.main.blueprints.one_dev.services.query_solver.query_solver import QuerySolver
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

code_gen_v2_bp = Blueprint("code_gen_v2_bp", url_prefix="/code-gen")


@code_gen_v2_bp.route("/solve-user-query")
@validate_client_version
@authenticate
@ensure_session_id(session_type="CODE_GENERATION_V2")
async def solve_user_query(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    response = await _request.respond()
    response.content_type = "text/event-stream"
    data = await QuerySolver().solve_query(payload=QuerySolverInput(**_request.json, session_id=session_id))

    async for data_block in data:
        await response.send("data: " + json.dumps(data_block.model_dump(mode="json")) + "\r\n\r\n")

    await response.eof()


@code_gen_v2_bp.route("/generate-inline-edit", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(session_type="CODE_GENERATION_V2")
async def generate_inline_edit(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    data = await InlineEditGenerator().create_and_start_job(
        payload=InlineEditInput(**_request.json, session_id=session_id, auth_data=auth_data)
    )
    return send_response({"job_id": data})
