from typing import Any, Dict

from sanic.log import logger
from torpedo import CONFIG
from tortoise.exceptions import DoesNotExist

from app.common.exception.exception import TeamNotFound
from app.common.services.authentication.jwt import JWTHandler
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputy_dev.models.dao.postgres.teams import Teams


class TeamLogin:
    @classmethod
    async def verify_token_data(cls, token_data: Dict[str, Any]):
        try:
            if not token_data:
                raise TeamNotFound("Invalid token")
            if not token_data.get("team_id"):
                raise TeamNotFound("Invalid token")
            if not token_data.get("advocacy_id"):
                raise TeamNotFound("Invalid token")
            if token_data["advocacy_id"] not in ConfigManager.configs["VALID_ADVOCACY_IDS"]:
                raise TeamNotFound("Invalid Advocate. Please connect with your advocate")
            try:
                await Teams.get(id=token_data["team_id"])  # check if team exists
            except DoesNotExist:
                raise TeamNotFound("Invalid token")
            return {"status": "VERIFIED"}
        except Exception as _ex:
            logger.exception(_ex)
            return {
                "status": "NOT_VERIFIED",
            }

    @classmethod
    async def verify_auth_token(cls, token: str):
        try:
            token_data = JWTHandler(signing_key=CONFIG.config.get("JWT_SECRET_KEY")).verify_token(token)
            return await cls.verify_token_data(token_data=token_data)
        except Exception as _ex:
            logger.exception(_ex)
            return {
                "status": "NOT_VERIFIED",
            }
