from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

from app.backend_common.utils.wrapper import exception_logger
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.deputy_dev.services.code_review.managers.extension_code_review_history_manager import (
    ExtensionCodeReviewHistoryManager,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.deputy_dev.models.ide_review_history_params import ReviewHistoryParams

extension_code_review = Blueprint("ide_code_review", "/extension-code-review")

config = CONFIG.config


@extension_code_review.route("/history", methods=["GET"])
@validate_client_version
@authenticate
async def code_review_history(_request: Request, auth_data: AuthData, **kwargs):
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


        review_history_params = ReviewHistoryParams(**query_params, user_team_id=auth_data.user_team_id)

        # Initialize manager and fetch reviews
        history_manager = ExtensionCodeReviewHistoryManager()
        reviews = await history_manager.fetch_reviews_by_filters(review_history_params)
        return send_response(reviews)

    except Exception as e:
        raise e
