from sanic import Blueprint, Sanic
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.one_dev.services.webhook_handlers.issue_code_generation_manager import (
    IssueCodeGenerationManager,
)

webhooks = Blueprint("webhooks", "/")

config = CONFIG.config


@webhooks.route("/issue", methods=["POST"])
async def issue_code_generation_api(_request: Request, **kwargs):
    payload = _request.custom_json()
    query_params = _request.request_params()
    headers = _request.headers
    request_id = headers.get("X-REQUEST-ID", "No request_id found")
    app = Sanic.get_app(CONFIG.config["NAME"])
    app.add_task(IssueCodeGenerationManager.handle_issue_comment(payload, query_params))
    return send_response(f"Processing Started with Request ID : {request_id}")
