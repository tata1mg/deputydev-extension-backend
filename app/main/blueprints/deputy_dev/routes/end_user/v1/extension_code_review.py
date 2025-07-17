from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.deputy_dev.services.code_review.extension_review.managers.extension_code_review_history_manager import (
    ExtensionCodeReviewHistoryManager,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.pre_processors.extension_review_pre_processor import (
    ExtensionReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.post_processors.extension_review_post_processor import (
    ExtensionReviewPostProcessor,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.deputy_dev.models.ide_review_history_params import ReviewHistoryParams
from app.main.blueprints.deputy_dev.services.code_review.extension_review.extension_review_manager import (
    ExtensionReviewManager,
)
from deputydev_core.utils.app_logger import AppLogger

extension_code_review = Blueprint("ide_code_review", "/extension-code-review")

config = CONFIG.config


@extension_code_review.route("/history", methods=["GET"])
@validate_client_version
# @authenticate
async def code_review_history(_request: Request, **kwargs):
    """
    Get code review history based on filters
    Query parameters:
    - user_team_id: Filter by user team ID
    - source_branch: Filter by source branch
    - target_branch: Filter by target branch
    - repo_id: Filter by repository ID
    """
    try:
        # Extract query parameters
        query_params = _request.request_params()
        review_history_params = ReviewHistoryParams(**query_params, user_team_id=1)

        # Initialize manager and fetch reviews
        history_manager = ExtensionCodeReviewHistoryManager()
        reviews = await history_manager.fetch_reviews_by_filters(review_history_params)
        return send_response(reviews)

    except Exception as e:
        raise e


@extension_code_review.route("/pre-process", methods=["POST"])
# @validate_client_version
# @authenticate
# async def pre_process_extension_review(request: Request, auth_data: AuthData, **kwargs):
async def pre_process_extension_review(request: Request, **kwargs):
    data = request.json
    processor = ExtensionReviewPreProcessor()
    # review_dto = await processor.pre_process_pr(data, user_team_id=auth_data.user_team_id)
    review_dto = await processor.pre_process_pr(data, user_team_id=data.get("user_team_id"))
    return send_response(review_dto)


@extension_code_review.route("/run-agent", methods=["POST"])
# @validate_client_version
# @authenticate
# async def run_extension_agent(request: Request, auth_data: AuthData, **kwargs):
async def run_extension_agent(request: Request, **kwargs):
    """
    Run an agent for extension code review.

    Payload:
    - review_id: The review ID from pre-process step
    - agent_type: The type of agent to run (e.g., "PERFORMANCE_OPTIMIZATION", "SECURITY", etc.)
    - type: Request type ("query" for initial request, "tool_use_response" for tool responses)
    - tool_use_response: Tool use response data (required when type is "tool_use_response")

    Returns:
    - For query type: Either tool request details or final result
    - For tool_use_response type: Either next tool request or final result
    """
    try:
        payload = request.json
        result = await ExtensionReviewManager.review_diff(payload)

        return send_response(result)

    except Exception as e:
        AppLogger.log_error(f"Error in review_diff_endpoint: {e}")
        return send_response(
            {
                "status": "SUCCESS",
            }
        )


@extension_code_review.route("/user-agents", methods=["GET"])
# @validate_client_version
# @authenticate
async def get_user_agents(_request: Request, **kwargs):
    """
    Get user agents for a specific user team.

    Query parameters:
    - user_team_id: The user team ID (automatically extracted from auth_data)

    Returns:
    - List of user agents associated with the user team
    """
    try:
        user_team_id = _request.request_params().get("user_team_id")
        user_agents = await UserAgentRepository.db_get(
            filters={"user_team_id": user_team_id},
        )

        # Convert to JSON-serializable format
        agents_response = []
        if user_agents:
            for agent in user_agents:
                agents_response.append(agent.model_dump(mode="json"))

        return send_response({"agents": agents_response, "count": len(agents_response)})

    except Exception as e:
        AppLogger.log_error(f"Error fetching user agents: {e}")
        raise e


@extension_code_review.route("/post-process", methods=["POST"])
@validate_client_version
# @authenticate
async def post_process_extension_review(request: Request, **kwargs):
    data = request.json
    processor = ExtensionReviewPostProcessor()
    await processor.post_process_pr(data, user_team_id=1)
    return send_response({"status": "SUCCESS"})
