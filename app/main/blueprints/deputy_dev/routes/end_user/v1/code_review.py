from sanic import Blueprint, Sanic
from sanic.log import logger
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.chat.smart_code_chat import (
    SmartCodeChatManager,
)
from app.main.blueprints.deputy_dev.services.code_review.code_review_trigger import (
    CodeReviewTrigger,
)
from app.main.blueprints.deputy_dev.services.code_review.pr_review_manager import (
    PRReviewManager,
)
from app.main.blueprints.deputy_dev.services.pr.update_pr_data_manager import (
    PRDataManager,
)
from app.main.blueprints.deputy_dev.services.sqs.meta_subscriber import MetaSubscriber

smart_code = Blueprint("smart_code", "/smart_code_review")

config = CONFIG.config


@smart_code.route("/", methods=["POST"])
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    query_params = _request.request_params()
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id
    response = await CodeReviewTrigger.perform_review(
        payload,
        prompt_version=query_params.get("prompt_version", "v2"),
        vcs_type=query_params.get("vcs_type", VCSTypes.bitbucket.value),
    )
    return send_response(response)


# For testing directly on local without queue, not used in PRODUCTION
@smart_code.route("/without_queue", methods=["POST"])
async def review_pr_in_sync(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id

    logger.info("Whitelisted request: {}".format(payload))
    await PRReviewManager.handle_event(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")


@smart_code.route("/chat", methods=["POST"])
async def chat_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    query_params = _request.request_params()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    # TODO - Unfulfilled parameter - comment
    await SmartCodeChatManager.chat(payload, vcs_type=query_params.get("vcs_type", VCSTypes.bitbucket.value))
    return send_response(f"Processing Started with Request ID : {request_id}")


@smart_code.route("/merge", methods=["POST"])
async def compute_merge_metrics(_request: Request, **kwargs):
    payload = _request.custom_json()
    query_params = _request.request_params()
    data = {"payload": payload, "query_params": query_params}
    await MetaSubscriber(config=config).publish(data)
    return send_response("Success")


@smart_code.route("/update_data", methods=["POST"])
async def compute_merge_metrics(_request: Request, **kwargs):
    app = Sanic.get_app(CONFIG.config["NAME"])
    app.add_task(PRDataManager().update_pr_data())
    return send_response("Success")
