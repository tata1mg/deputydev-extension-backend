from sanic import Blueprint
from sanic_ext import validate
from torpedo import Request, send_response

from app.managers.smartCodeReview import SmartCodeManager
from app.models.smart_code import SmartCodeReqeustModel
from app.utils import request_logger

smart_code = Blueprint("smart_code", "/smart_code_review")


@smart_code.route("/", methods=["GET"])
@validate(query=SmartCodeReqeustModel)
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.request_params()
    request_id = request_logger(_request)
    message = await SmartCodeManager.process_pr_review(payload, request_id)
    return send_response(message)


@smart_code.route("/chat", methods=["GET"])
@validate(query=SmartCodeReqeustModel)
async def chat_assistance_api(_request: Request, **kwargs):
    payload = _request.request_params()
    request_id = request_logger(_request)
    message = await SmartCodeManager.chat(payload, request_id)
    return send_response(message)
