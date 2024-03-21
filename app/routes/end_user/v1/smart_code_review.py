from sanic import Blueprint
from sanic.log import logger
from sanic_ext import validate
from torpedo import Request, send_response

from app.managers.smartCodeChat import SmartCodeChatManager
from app.managers.smartCodeReview import SmartCodeManager
from app.models.smart_code import SmartCodeReqeustModel
from app.utils import get_comment

smart_code = Blueprint("smart_code", "/smart_code_review")


@smart_code.route("/", methods=["GET"])
@validate(query=SmartCodeReqeustModel)
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.request_params()
    message = await SmartCodeManager.process_pr_review(payload)
    return send_response(message)


@smart_code.route("/chat", methods=["POST"])
async def chat_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    #TODO - This should moved to manager. Routes should act only as a proxy.
    comment_payload = get_comment(payload)
    logger.info(f"Comment payload: {comment_payload}")
    # status = validate_hash(payload)
    # if not status:
    #     raise ValueError("Signatures do not match.")
    # request_id = request_logger(_request)
    message = await SmartCodeChatManager.chat(payload, comment_payload)
    return send_response(message)
