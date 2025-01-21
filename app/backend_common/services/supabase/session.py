from typing import Any, Dict

from postgrest.exceptions import APIError
from torpedo import CONFIG

from app.backend_common.repository.users.user_service import UserService
from app.backend_common.services.supabase.auth import SupabaseAuth
from app.common.services.authentication.jwt import JWTHandler

from .client import supabase

JWT_SECRET = CONFIG.config["JWT_SECRET_KEY"]


class SupabaseSession:
    @classmethod
    async def get_session_by_device_code(cls, headers: Dict) -> Dict[str, Any]:
        """
        Query the cli_sessions table for a session matching the given device code.

        Args:
            headers: The headers containing the device code

        Returns:
            Dict[str, Any]: A dictionary containing either:
                - 'jwt_token': JWT token containing session data if found
                - 'error': Error dict if an error occurred
        """
        device_code = headers.get("X-Device-Code")
        if not device_code:
            return {
                "error": {"message": "Device code missing in headers", "code": "MISSING_DEVICE_CODE", "status": 400}
            }

        try:
            response = supabase.table("cli_sessions").select("*").eq("device_code", device_code).single().execute()
            data = response.data if response else None

            if not data:
                return {"error": {"message": "No session data found", "code": "NO_DATA", "status": 404}}

            access_token = data["access_token"]
            token_data = await SupabaseAuth.verify_auth_token(access_token)

            # Extract email from token data
            email = token_data["user_email"]

            # Fetch the registered user ID based on the email
            user = await UserService.db_get(filters={"email": email}, fetch_one=True)

            # Add email and user_id to session data
            data["email"] = email
            data["user_id"] = user.id

            # Encode the session data into a JWT token
            jwt_token = JWTHandler(signing_key=JWT_SECRET, algorithm="HS256").create_token(payload=data)

            return {"jwt_token": jwt_token}

        except APIError as e:
            return {"error": {"message": str(e), "code": getattr(e, "code", "UNKNOWN_ERROR"), "status": 500}}
