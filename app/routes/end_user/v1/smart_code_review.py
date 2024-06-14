from sanic import Blueprint
from sanic.log import logger
from sanic_ext import validate
from torpedo import CONFIG, Request, send_response

from app.managers.deputy_dev import CodeReviewManager
from app.managers.deputy_dev.code_review_trigger import CodeReviewTrigger
from app.managers.scrit.smartCodeChat import SmartCodeChatManager
from app.models.smart_code import SmartCodeReqeustModel

smart_code = Blueprint("smart_code", "/smart_code_review")

config = CONFIG.config


@smart_code.route("/", methods=["POST"])
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id
    response = await CodeReviewTrigger.perform_review(payload)
    return send_response(response)


# For testing directly on local without queue, not used in PRODUCTION
@smart_code.route("/without_queue", methods=["POST"])
async def review_pr_in_sync(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id

    logger.info("Whitelisted request: {}".format(payload))
    await CodeReviewManager.handle_event(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")


@smart_code.route("/chat", methods=["POST"])
async def chat_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    # TODO - Unfulfilled parameter - comment
    await SmartCodeChatManager.chat(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")
