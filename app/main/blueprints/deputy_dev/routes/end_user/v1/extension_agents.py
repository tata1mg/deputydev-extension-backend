from sanic import Blueprint
from torpedo import CONFIG, Request, send_response
from app.main.blueprints.deputy_dev.services.code_review.extension_review.managers.agent_manager import (
    AgentManager,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.deputy_dev.models.agent_crud_params import AgentCreateParams, AgentUpdateParams
from deputydev_core.utils.app_logger import AppLogger
from pydantic import ValidationError
from torpedo.exceptions import BadRequestException

agents = Blueprint("agents", "/agent")

config = CONFIG.config


@agents.route("/list", methods=["GET"])
@validate_client_version
@authenticate
async def get_user_agents(_request: Request, auth_data: AuthData, **kwargs):
    """
    Get user agents for a specific user team.

    Query parameters:
    - user_team_id: The user team ID (automatically extracted from auth_data)

    Returns:
    - List of user agents associated with the user team
    """
    try:
        agents_response = await AgentManager.get_or_create_agents(user_team_id=auth_data.user_team_id)
        return send_response({"agents": agents_response, "count": len(agents_response)})
    except Exception as e:
        AppLogger.log_error(f"Error fetching user agents: {e}")
        raise e


@agents.route("/", methods=["POST"])
@validate_client_version
@authenticate
async def create_agent(_request: Request, auth_data: AuthData, **kwargs):
    try:
        payload = _request.custom_json()
        payload = AgentCreateParams(**payload, user_team_id=2)
        agent_manager = AgentManager()
        agent = await agent_manager.create_agent(payload)
        return send_response(agent)
    except ValidationError as e:
        raise BadRequestException(f"Invalid parameters: {e}")


@agents.route("/<agent_id:int>", methods=["PATCH"])
@validate_client_version
@authenticate
async def update_agent(_request: Request, agent_id, auth_data: AuthData, **kwargs):
    try:
        """Update an existing agent with the provided parameters."""
        payload = _request.custom_json()
        payload = AgentUpdateParams(**payload, id=agent_id, user_team_id=2)
        agent_manager = AgentManager()
        agent = await agent_manager.update_agent(payload)
        return send_response(agent)
    except ValidationError as e:
        raise BadRequestException(f"Invalid parameters: {e}")


@agents.route("/<agent_id:int>", methods=["DELETE"])
@validate_client_version
@authenticate
async def delete_agent(_request: Request, agent_id, auth_data: AuthData, **kwargs):
    """Delete an agent by its ID."""
    try:
        agent_manager = AgentManager()
        response = await agent_manager.delete_agent(agent_id)
        return send_response(response)
    except Exception as e:
        raise e
