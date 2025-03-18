from typing import Any, Dict

from app.main.blueprints.one_dev.services.auth.login import Login


class Auth:
    @classmethod
    async def extract_and_verify_token(cls, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        authorization_header = headers.get("Authorization")
        if not authorization_header:
            raise Exception("Authorization header is missing")

        # decode encrypted session data and get the supabase access token
        encrypted_session_data = authorization_header.split(" ")[1]
        enable_grace_period = payload.get("enable_grace_period") or False
        result = await Login.verify_auth_token(encrypted_session_data, enable_grace_period=enable_grace_period)
        return result
