from typing import Any, Dict

from sanic.log import logger
from torpedo import CONFIG
from tortoise.exceptions import DoesNotExist

from app.backend_common.services.supabase.auth import SupabaseAuth
from app.common.exception.exception import TeamNotFound
from app.common.services.authentication.jwt import JWTHandler
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputy_dev.models.dao.postgres.teams import Teams
from torpedo.exceptions import BadRequestException


class Login:
    @classmethod
    async def verify_auth_token(cls, headers):
        try:
            authorization_header = headers.get("Authorization")
            if not authorization_header:
                raise Exception("Authorization header is missing")

            # decode the JWT token and get the supabase access token
            jwt = authorization_header.split(" ")[1]
            session_data = JWTHandler(signing_key=CONFIG.config["JWT_SECRET_KEY"]).verify_token(jwt)
            access_token = session_data.get("access_token")
            print(access_token)
            response = await SupabaseAuth.verify_auth_token(access_token)
            if not response["valid"]:
                raise BadRequestException("Auth token not verified")
            return {
                "status": "VERIFIED",
            }
        except Exception as _ex:
            return {
                "status": "NOT_VERIFIED",
                "error_message": str(_ex),
            }
