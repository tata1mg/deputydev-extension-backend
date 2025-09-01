from typing import Any

from sanic import Blueprint
from sanic.log import logger
from sanic.response import JSONResponse
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import Response

from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.main.blueprints.deputy_dev.services.ab_analysis.ab_analysis_svc import (
    AbAnalysisFetchingData,
)

ab_analysis = Blueprint("ab_analysis", "/ab_analysis")


@ab_analysis.route("/csv-data", methods=["GET"])
@openapi.definition(
    summary="Fetches AB analysis data based on query phase and ab analysis time",
    description="Returns ab analysis as CSV data in the `data` field. The `query_phase` can be 'phase1' or 'phase2' and `ab_analysis_time` can be 'approval' or 'merge'",
    response=[
        Response(
            content={
                "application/json": {
                    "data": openapi.String(description="CSV data in string format"),
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful"),
                    "status_code": openapi.Integer(description="HTTP status code (200 for success)"),
                }
            },
            description="Success response with CSV data",
            status=200,
        ),
        Response(
            content={
                "application/json": {
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful"),
                    "status_code": openapi.Integer(description="HTTP status code (400 for error)"),
                    "error": openapi.Object(
                        properties={
                            "message": openapi.String(description="Error message"),
                            "errors": openapi.Array(
                                items=openapi.Object(
                                    properties={"message": openapi.String(description="Detailed error message")}
                                )
                            ),
                        }
                    ),
                }
            },
            description="Error response with detailed error message",
            status=400,
        ),
    ],
)
async def fetching_ab_analysis_data(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    logger.debug(query_params)
    response = await AbAnalysisFetchingData.get_ab_analysis_data(query_params)
    return send_response(response)
