from typing import Any, Dict

from jwt import ExpiredSignatureError, InvalidTokenError
from torpedo import CONFIG
from torpedo.exceptions import BadRequestException

from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.common.constants.constants import AuthStatus
from app.common.services.authentication.jwt import JWTHandler


class Login:
    @classmethod
    async def verify_auth_token(cls, jwt_token: str) -> Dict[str, Any]:
        try:
            session_data = JWTHandler(signing_key=CONFIG.config["JWT_SECRET_KEY"]).verify_token(jwt_token)
            access_token = session_data.get("access_token")
            response = await SupabaseAuth.verify_auth_token(access_token)
            if not response["valid"]:
                raise BadRequestException("Auth token not verified")
            return {
                "status": AuthStatus.VERIFIED.value,
            }
        except ExpiredSignatureError:
            return {
                "status": AuthStatus.NOT_VERIFIED.value,
                "error_message": "Token has expired.",
            }
        except InvalidTokenError:
            return {
                "status": AuthStatus.NOT_VERIFIED.value,
                "error_message": "Invalid token format.",
            }
        except Exception as _ex:
            return {
                "status": AuthStatus.NOT_VERIFIED.value,
                "error_message": str(_ex),
            }
