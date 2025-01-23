from typing import Any, Dict

from app.main.blueprints.one_dev.services.auth.login import Login


class Auth:
    @classmethod
    async def extract_and_verify_token(cls, headers: Dict[str, str]) -> Dict[str, Any]:
        authorization_header = headers.get("Authorization")
        if not authorization_header:
            raise Exception("Authorization header is missing")

        # decode the JWT token and get the supabase access token
        jwt = authorization_header.split(" ")[1]
        result = await Login.verify_auth_token(jwt)
        return result
