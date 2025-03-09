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
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

query_solver = Blueprint("query_solver", "/")


@query_solver.route("/solve-user-query")
@authenticate
@ensure_session_id
async def solve_user_query(_request: Request, auth_data: AuthData, session_id: int, **kwargs: Any):
    response = await _request.respond()
    response.content_type = "text/event-stream"
    data = await QuerySolver().solve_query(payload=QuerySolverInput(**_request.json, session_id=session_id))

    async for data_block in data:
        await response.send("data: " + json.dumps(data_block.model_dump(mode="json")) + "\r\n\r\n")

    await response.eof()


@query_solver.route("/generate-inline-edit", methods=["POST"])
@authenticate
@ensure_session_id
async def generate_inline_edit(_request: Request, auth_data: AuthData, session_id: int, **kwargs: Any):
    data = await InlineEditGenerator().create_and_start_job(
        payload=InlineEditInput(**_request.json, session_id=session_id, auth_data=auth_data)
    )
    return send_response({"job_id": data})
