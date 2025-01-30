import json
from typing import Any, Dict

from jwt import ExpiredSignatureError, InvalidTokenError
from torpedo.exceptions import BadRequestException

from app.backend_common.services.auth.session_encryption_service import (
    SessionEncryptionService,
)
from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.common.constants.auth import AuthStatus


class Login:
    @classmethod
    async def verify_auth_token(cls, encrypted_session_data: str) -> Dict[str, Any]:
        try:
            # first decrypt the encrypted session data using session encryption service
            session_data_string = SessionEncryptionService.decrypt(encrypted_session_data)
            # convert back to json object
            session_data = json.loads(session_data_string)
            # extract supabase access token
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
