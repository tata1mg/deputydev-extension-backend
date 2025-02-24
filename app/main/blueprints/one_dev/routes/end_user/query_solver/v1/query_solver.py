import json
from typing import Any

from sanic import Blueprint
from torpedo import Request

from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    QuerySolverInput,
)
from app.main.blueprints.one_dev.services.query_solver.query_solver import QuerySolver

query_solver = Blueprint("query_solver", "/")


@query_solver.route("/solve-user-query")
async def solve_user_query(_request: Request, **kwargs: Any):
    response = await _request.respond()
    response.content_type = "text/event-stream"
    data = await QuerySolver().solve_query(payload=QuerySolverInput(**_request.json))

    await response.send(
        "data: "
        + json.dumps({"type": "RESPONSE_METADATA", "content": {"query_id": 110, "session_id": 213}})
        + "\r\n\r\n"
    )

    async for data_block in data.parsed_content:
        await response.send("data: " + json.dumps(data_block.model_dump(mode="json")) + "\r\n\r\n")
        # await response.send("data: " + "GAGAGAGGA" + "\r\n\r\n")

    await response.eof()
