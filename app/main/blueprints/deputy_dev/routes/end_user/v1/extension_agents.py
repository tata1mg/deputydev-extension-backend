from sanic import Blueprint
from torpedo import CONFIG, Request, send_response
from app.main.blueprints.deputy_dev.services.code_review.extension_review.managers.agent_manager import (
    AgentManager,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.deputy_dev.models.agent_crud_params import AgentParams
agents = Blueprint("agents", "/agent")

config = CONFIG.config


@agents.route("/", methods=["POST"])
@validate_client_version
# @authenticate
async def create_agent(_request: Request, **kwargs):
    try:
        payload = _request.custom_json()
        payload = AgentParams(**payload, user_team_id=1)
        agent_manager = AgentManager()
        agent = await agent_manager.create_agent(payload)
        return send_response(agent)
    except Exception as e:
        raise e


@agents.route("/<agent_id:int>", methods=["PATCH"])
@validate_client_version
# @authenticate
async def update_agent(_request: Request, agent_id, **kwargs):
    """Update an existing agent with the provided parameters."""
    try:
        payload = _request.custom_json()
        payload = AgentParams(**payload, id=agent_id, user_team_id=1)
        agent_manager = AgentManager()
        agent = await agent_manager.update_agent(payload)
        return send_response(agent)
    except Exception as e:
        raise e


@agents.route("/<agent_id:int>", methods=["DELETE"])
@validate_client_version
# @authenticate
async def delete_agent(_request: Request, agent_id, **kwargs):
    """Delete an agent by its ID."""
    try:
        agent_manager = AgentManager()
        response = await agent_manager.delete_agent(agent_id)
        return send_response(response)
    except Exception as e:
        raise e
