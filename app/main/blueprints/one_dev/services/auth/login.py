import json
from typing import Any, Dict

from jwt import ExpiredSignatureError, InvalidTokenError

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
                return {"status": AuthStatus.NOT_VERIFIED.value}
            return {"status": AuthStatus.VERIFIED.value}
        # TODO: add refresh token logic.
        except ExpiredSignatureError:
            # refresh the current session
            refresh_session_data = await SupabaseAuth.refresh_session(session_data.get("refresh_token"))
            # update the session data with the refreshed access and refresh tokens
            session_data["access_token"] = refresh_session_data["access_token"]
            session_data["refresh_token"] = refresh_session_data["refresh_token"]
            # return the refreshed session data
            encrypted_session_data = SessionEncryptionService.encrypt(json.dumps(session_data))
            return {
                "status": AuthStatus.EXPIRED.value,
                "encrypted_session_data": encrypted_session_data,
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
