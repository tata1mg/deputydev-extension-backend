from sanic import Blueprint
from sanic_ext import validate
from torpedo import Request, send_response

from app.managers.scrit.smartCodeChat import SmartCodeChatManager
from app.managers.scrit.smartCodeReview import SmartCodeManager
from app.models.smart_code import SmartCodeReqeustModel

smart_code = Blueprint("smart_code", "/smart_code_review")


@smart_code.route("/", methods=["GET"])
@validate(query=SmartCodeReqeustModel)
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.request_params()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    await SmartCodeManager.process_pr_review(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")


@smart_code.route("/chat", methods=["POST"])
async def chat_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    # TODO - This should moved to manager. Routes should act only as a proxy.
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    await SmartCodeChatManager.chat(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")
