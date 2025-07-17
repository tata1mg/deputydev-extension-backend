from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.deputy_dev.services.code_review.extension_review.managers.agent_manager import (
    AgentManager,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.pre_processors.extension_review_pre_processor import (
    ExtensionReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.post_processors.extension_review_post_processor import (
    ExtensionReviewPostProcessor,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.deputy_dev.models.agent_crud_params import AgentParams
from app.main.blueprints.deputy_dev.services.code_review.extension_review.extension_review_manager import (
    ExtensionReviewManager,
)
from deputydev_core.utils.app_logger import AppLogger

agents = Blueprint("agents", "/agent")

config = CONFIG.config


@agents.route("/", methods=["POST"])
@validate_client_version
# @authenticate
async def create_agent(_request: Request, **kwargs):
    """
    Get code review history based on filters
    Query parameters:
    - user_team_id: Filter by user team ID
    - source_branch: Filter by source branch
    - target_branch: Filter by target branch
    - repo_id: Filter by repository ID
    """
    try:
        payload = _request.custom_json()
        payload = AgentParams(**payload, user_team_id=1)
        agent_manager = AgentManager()
        agent = await agent_manager.create_agent(payload)
        return send_response(agent)
    except Exception as e:
        raise e
