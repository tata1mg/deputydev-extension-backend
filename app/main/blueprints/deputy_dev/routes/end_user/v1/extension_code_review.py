from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

from app.backend_common.utils.wrapper import exception_logger

from app.main.blueprints.deputy_dev.services.code_review.code_review_trigger import (
    CodeReviewTrigger,
)

smart_code = Blueprint("smart_code", "/extension-code-review")

config = CONFIG.config


@smart_code.route("/review-history", methods=["GET"])
@exception_logger
async def code_review_history(_request: Request, **kwargs):
    headers = _request.headers
    query_params = _request.request_params()
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    response = await CodeReviewTrigger.code_review_history(payload, query_params=query_params)
    return send_response(response)

