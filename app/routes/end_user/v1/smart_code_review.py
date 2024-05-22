from datetime import datetime, timezone

from sanic import Blueprint
from sanic.log import logger
from sanic_ext import validate
from torpedo import CONFIG, Request, send_response

from app.managers.scrit.smartCodeChat import SmartCodeChatManager
from app.models.smart_code import SmartCodeReqeustModel
from app.sqs.genai_subscriber import GenaiSubscriber

smart_code = Blueprint("smart_code", "/smart_code_review")

config = CONFIG.config


@smart_code.route("/", methods=["GET"])
@validate(query=SmartCodeReqeustModel)
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.request_params()
    headers = _request.headers

    # Get the current datetime in UTC timezone
    current_datetime = datetime.now(timezone.utc)
    # Format the datetime as per the specified format
    formatted_datetime_str = current_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

    payload["request_time"] = str(formatted_datetime_str)
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id
    if payload.get("repo_name") in config.get("WHITELISTED_REPOS"):
        logger.info("Whitelisted request: {}".format(payload))
        await GenaiSubscriber(config=config).publish(payload=payload)
        return send_response(f"Processing Started with Request ID : {request_id}")
    else:
        logger.info("Blocked request: {}".format(payload))
        return send_response(status_code=422, data=f'Currently we are not serving: {payload.get("repo_name")}')


@smart_code.route("/chat", methods=["POST"])
async def chat_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    # TODO - Unfulfilled parameter - comment
    await SmartCodeChatManager.chat(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")
