from sanic import Blueprint, Sanic
from sanic.log import logger
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.deputy_dev.services.chat.smart_code_chat import (
    SmartCodeChatManager,
)
from app.main.blueprints.deputy_dev.services.code_review.code_review_trigger import (
    CodeReviewTrigger,
)
from app.main.blueprints.deputy_dev.services.code_review.pr_review_manager import (
    PRReviewManager,
)
from app.main.blueprints.deputy_dev.services.pr.backfill_data_manager import (
    BackfillManager,
)
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_trigger import (
    StatsCollectionTrigger,
)

smart_code = Blueprint("smart_code", "/smart_code_review")

config = CONFIG.config


@smart_code.route("/", methods=["POST"])
async def pool_assistance_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    headers = _request.headers
    query_params = _request.request_params()
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id
    response = await CodeReviewTrigger.perform_review(payload, query_params=query_params)
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
    payload["request_id"] = request_id
    # TODO - Unfulfilled parameter - comment
    await SmartCodeChatManager.chat(payload, query_params)
    return send_response(f"Processing Started with Request ID : {request_id}")


@smart_code.route("/stats-collection", methods=["POST"])
async def compute_pr_close_metrics(_request: Request, **kwargs):
    logger.info("Request received for stats-collection")
    payload = _request.custom_json()
    query_params = _request.request_params()
    await StatsCollectionTrigger().select_stats_and_publish(payload=payload, query_params=query_params)
    return send_response("Success")


# The below url is temporary to carter the merge flow, once the "/stats-collection" url is integrated,
# the API below will be deprecated.
@smart_code.route("/merge", methods=["POST"])
async def compute_merge_metrics(_request: Request, **kwargs):
    payload = _request.custom_json()
    query_params = _request.request_params()
    await StatsCollectionTrigger().select_stats_and_publish(payload=payload, query_params=query_params)
    return send_response("Success")


# The route defined below acts like a script, which when called upon is used to backfill data.
# These are supposed to be one time activity, so please use this route accordingly
@smart_code.route("/backfill_pr_data", methods=["POST"])
async def update_pr_data(_request: Request, **kwargs):
    query_params = _request.request_params()
    app = Sanic.get_app(CONFIG.config["NAME"])
    if query_params.get("type") == "pr_state_experiments_update":
        app.add_task(BackfillManager().backfill_expermients_data(query_params))
    elif query_params.get("type") == "pr_state_pullrequest_update":
        app.add_task(BackfillManager().backfill_pullrequests_data(query_params))
    elif query_params.get("type") == "pr_approval_time_pullrequest_update":
        app.add_task(BackfillManager().backfill_pr_approval_time(query_params))
    else:
        app.add_task(BackfillManager().backfill_comments_count_in_experiments_table(query_params))
    return send_response("Success")
