import asyncio

from sanic import Blueprint, Sanic
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.deputy_dev.services.backfill.agent_mapping_backfill_manager import AgentMappingBackfillManager
from app.main.blueprints.deputy_dev.services.repository.pr.backfill_data_manager import (
    BackfillManager,
)


backfill = Blueprint("backfil", "/backfill")


@backfill.route("/agent_mapping", methods=["POST"])
async def update_pr_data(_request: Request, **kwargs):
    payload = _request.custom_json()
    asyncio.create_task(AgentMappingBackfillManager.backfill_data(payload))
    return send_response("Processing Started")
