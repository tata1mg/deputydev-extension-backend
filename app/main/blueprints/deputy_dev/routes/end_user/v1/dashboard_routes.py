from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse
from sanic_ext import openapi
from sanic_ext.extensions.openapi.definitions import Response

from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.main.blueprints.deputy_dev.models.analytics import AnalyticsData
from app.main.blueprints.deputy_dev.services.analytics.analytics_service import (
    AnalyticsManager,
)
from app.main.blueprints.deputy_dev.services.dashboard.dashboard_filters import (
    DashboardFiltersManager,
)

console = Blueprint("console", "/console")


@console.route("/analytics", methods=["GET"])
@openapi.definition(
    summary="Fetch analytics data based on team_id, workspace_id, repo_ids, graph_type, time_filter, and interval_filter passed as query parameters.",
    description=(
        "This API returns a list of dictionaries in the `data` field based on the specified `graph_type`. "
        "The `graph_type` parameter determines the structure and content of the returned data, which could include "
        "PR score data, comment types data, or reviewed vs rejected data."
    ),
    response=[
        Response(
            content={
                "application/json": {
                    "data": AnalyticsData.model_json_schema(),
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful."),
                    "status_code": openapi.Integer(description="HTTP status code (200 for success)."),
                }
            },
            description="Successful response containing the analytics data.",
            status=200,
        ),
        Response(
            content={
                "application/json": {
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful."),
                    "status_code": openapi.Integer(description="HTTP status code (400 for error)."),
                    "error": openapi.Object(
                        properties={
                            "message": openapi.String(description="High-level error message describing the issue."),
                            "errors": openapi.Array(
                                items=openapi.Object(
                                    properties={
                                        "message": openapi.String(
                                            description="Detailed error message providing additional context."
                                        )
                                    }
                                ),
                                description="List of detailed error messages.",
                            ),
                        },
                        description="Detailed information about the error.",
                    ),
                }
            },
            description="Error response containing detailed error information.",
            status=400,
        ),
    ],
)
async def get_analytics_data(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    response = await AnalyticsManager.handle_analytics_data(query_params=query_params)
    return send_response(response, headers={"Access-Control-Allow-Origin": "*"})


@console.route("/teams", methods=["GET"])
@openapi.definition(
    summary="Fetches teams data on the basis of user_id passed through query params",
    description="Returns a list of teams in the `data` field. The `user_id` should be provided as an integer.",
    response=[
        Response(
            content={
                "application/json": {
                    "data": openapi.Array(
                        items=openapi.Object(
                            properties={
                                "team_id": openapi.Integer(description="Unique identifier for the team"),
                                "team_name": openapi.String(description="Name of the team"),
                            }
                        ),
                        description="List of teams in dictionary format",
                    ),
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful"),
                    "status_code": openapi.Integer(description="HTTP status code (200 for success)"),
                }
            },
            description="Success response with teams data",
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
async def get_teams(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    response = await DashboardFiltersManager.get_teams(query_params)
    return send_response(response, headers={"Access-Control-Allow-Origin": "*"})


@console.route("/workspaces", methods=["GET"])
@openapi.definition(
    summary="Fetches workspaces data on the basis of team_id passed through query params",
    description="Returns a list of workspaces in the `data` field. The `team_id` should be provided as an integer.",
    response=[
        Response(
            content={
                "application/json": {
                    "data": openapi.Array(
                        items=openapi.Object(
                            properties={
                                "workspace_id": openapi.Integer(description="Unique identifier for the workspace"),
                                "workspace_name": openapi.String(description="Name of the workspace"),
                            }
                        ),
                        description="List of workspaces in dictionary format",
                    ),
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful"),
                    "status_code": openapi.Integer(description="HTTP status code (200 for success)"),
                }
            },
            description="Success response with workspaces data",
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
async def get_workspaces(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    response = await DashboardFiltersManager.get_workspaces(query_params)
    return send_response(response, headers={"Access-Control-Allow-Origin": "*"})


@console.route("/repos", methods=["GET"])
@openapi.definition(
    summary="Fetches repos data on the basis of workspace_id passed through query params",
    description="Returns a list of repos in the `data` field. The `workspace_id` should be provided as an integer.",
    response=[
        Response(
            content={
                "application/json": {
                    "data": openapi.Array(
                        items=openapi.Object(
                            properties={
                                "repo_id": openapi.Integer(description="Unique identifier for the repo"),
                                "repo_name": openapi.String(description="Name of the repo"),
                            }
                        ),
                        description="List of repos in dictionary format",
                    ),
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful"),
                    "status_code": openapi.Integer(description="HTTP status code (200 for success)"),
                }
            },
            description="Success response with repos data",
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
async def get_repos(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    response = await DashboardFiltersManager.get_repos(query_params)
    return send_response(response, headers={"Access-Control-Allow-Origin": "*"})


@console.route("/pull_requests", methods=["GET"])
@openapi.definition(
    summary="Fetches pull requests data on the basis of repo_ids passed through query params",
    description="Returns a list of pull requests in the `data` field. The `repo_ids` should be provided as an integer.",
    response=[
        Response(
            content={
                "application/json": {
                    "data": openapi.Array(
                        items=openapi.Object(
                            properties={
                                "pr_id": openapi.Integer(description="Unique identifier for the pr"),
                                "pr_name": openapi.String(description="Name of the pr"),
                            }
                        ),
                        description="List of pull requests in dictionary format",
                    ),
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful"),
                    "status_code": openapi.Integer(description="HTTP status code (200 for success)"),
                }
            },
            description="Success response with pull requests data",
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
async def get_prs(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    response = await AnalyticsManager.handle_prs_data(query_params)
    return send_response(response, headers={"Access-Control-Allow-Origin": "*"})


@console.route("/tiles_data", methods=["GET"])
@openapi.definition(
    summary="Fetches tile data on the basis of team_id, tile_type and time_filter passed through query params",
    description="Returns tile data, tile can be number of merged prs or number of raised prs or code review time.",
    response=[
        Response(
            content={
                "application/json": {
                    "data": openapi.Array(
                        items=openapi.Object(
                            properties={
                                "num_raised_prs": openapi.Integer(
                                    description="Number of raised pull requests.",
                                ),
                                "num_merged_prs": openapi.Integer(
                                    description="Number of merged pull requests.",
                                ),
                                "code_review_time": openapi.Integer(
                                    description="Average code review time in hours.",
                                ),
                            },
                        ),
                        description="This api can return any of the tile data based on the tile type",
                    ),
                    "is_success": openapi.Boolean(description="Indicates whether the request was successful"),
                    "status_code": openapi.Integer(description="HTTP status code (200 for success)"),
                }
            },
            description="Success response with tile data",
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
async def get_tiles(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    response = await DashboardFiltersManager.get_tiles(query_params)
    return send_response(response, headers={"Access-Control-Allow-Origin": "*"})
