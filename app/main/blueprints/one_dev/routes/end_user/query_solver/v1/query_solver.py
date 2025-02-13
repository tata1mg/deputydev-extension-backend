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

    async for data_block in data.raw_llm_response:
        await response.send("data: " + str(data_block.model_dump(mode="json")) + "\r\n\r\n")
        # await response.send("data: " + "GAGAGAGGA" + "\r\n\r\n")

    await response.eof()
