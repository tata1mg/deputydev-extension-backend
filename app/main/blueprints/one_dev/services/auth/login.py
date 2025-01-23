from typing import Any, Dict

from torpedo.exceptions import BadRequestException

from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.common.services.authentication.jwt import JWTHandler
from app.common.utils.config_manager import ConfigManager


class Login:
    @classmethod
    async def verify_auth_token(cls, jwt_token: str) -> Dict[str, Any]:
        try:
            session_data = JWTHandler(signing_key=ConfigManager.config["JWT_SECRET_KEY"]).verify_token(jwt_token)
            access_token = session_data.get("access_token")
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
