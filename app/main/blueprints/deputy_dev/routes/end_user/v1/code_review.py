import asyncio
from typing import Any

from deputydev_core.services.chunking.chunker.base_chunker import FileChunkCreator
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from sanic import Blueprint, Sanic
from sanic.log import logger
from sanic.response import JSONResponse

from app.backend_common.utils.sanic_wrapper import CONFIG, Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.backend_common.utils.wrapper import exception_logger
from app.main.blueprints.deputy_dev.services.chat.smart_code_chat import (
    SmartCodeChatManager,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.code_review_trigger import (
    CodeReviewTrigger,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.pr_review_manager import (
    PRReviewManager,
)
from app.main.blueprints.deputy_dev.services.repository.pr.backfill_data_manager import (
    BackfillManager,
)

smart_code = Blueprint("smart_code", "/smart_code_review")

config = CONFIG.config


@smart_code.route("/", methods=["POST"])
@exception_logger
async def publish_code_review(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    payload = _request.custom_json()
    headers = _request.headers
    query_params = _request.request_params()
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id
    response = await CodeReviewTrigger.perform_review(payload, query_params=query_params)
    return send_response(response)


# For testing directly on local without queue, not used in PRODUCTION
@smart_code.route("/without_queue", methods=["POST"])
async def review_pr_in_sync(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id

    logger.info("Whitelisted request: {}".format(payload))
    await PRReviewManager.handle_event(payload)
    return send_response(f"Processing Started with Request ID : {request_id}")


@smart_code.route("/chat", methods=["POST"])
@exception_logger
async def chat_assistance_api(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    payload = _request.custom_json()
    query_params = _request.request_params()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id
    # TODO - Unfulfilled parameter - comment
    asyncio.ensure_future(SmartCodeChatManager.chat(payload, query_params))
    return send_response(f"Processing Started with Request ID : {request_id}")


# The route defined below acts like a script, which when called upon is used to backfill data.
# These are supposed to be one time activity, so please use this route accordingly
@smart_code.route("/backfill_pr_data", methods=["POST"])
async def update_pr_data(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
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


@smart_code.route("/test_chunking", methods=["POST"])
async def test_chunking(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    payload = _request.custom_json()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    payload["request_id"] = request_id
    logger.info("Whitelisted request: {}".format(payload))
    root_dir = payload["repo_dir"]
    path = payload["path"]
    chunks = FileChunkCreator.create_chunks(path, root_dir, use_new_chunking=True)
    rendered_chunks = render_snippet_array(chunks)
    return send_response(f"Processing Started with Request ID : {dict({'result': rendered_chunks})}")
