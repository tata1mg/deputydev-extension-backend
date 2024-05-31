from sanic import Blueprint
from sanic.log import logger
from sanic_ext import validate
from torpedo import CONFIG, Request, send_response

from app.managers.deputy_dev import CodeReviewManager
from app.managers.deputy_dev.code_review_trigger import CodeReviewTrigger
from app.managers.scrit.smartCodeChat import SmartCodeChatManager
from app.models.smart_code import SmartCodeReqeustModel
from app.utils import get_request_time

smart_code = Blueprint("smart_code", "/smart_code_review")

config = CONFIG.config


@smart_code.route("/", methods=["POST"])
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    response = await CodeReviewTrigger.perform_review(payload)
    return send_response(response)


# For testing directly on local without queue, not used in PRODUCTION
@smart_code.route("/without_queue", methods=["GET"])
@validate(query=SmartCodeReqeustModel)
async def review_pr_in_sync(_request: Request, **kwargs):
    payload = _request.request_params()
    headers = _request.headers
    payload["request_time"] = get_request_time()
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    if True:
        logger.info("Whitelisted request: {}".format(payload))
        await CodeReviewManager.handle_event(payload)
        return send_response(f"Processing Started with Request ID : {request_id}")
    else:
        logger.info("Blocked request: {}".format(payload))
        return send_response(data=f'Currently we are not serving: {payload.get("repo_name")}')


@smart_code.route("/chat", methods=["POST"])
async def chat_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    # TODO - Unfulfilled parameter - comment
    await SmartCodeChatManager.chat(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")
