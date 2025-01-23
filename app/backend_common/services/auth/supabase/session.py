from typing import Any, Dict


from app.backend_common.repository.users.user_service import UserService
from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.common.services.authentication.jwt import JWTHandler

from app.backend_common.services.auth.supabase.client import SupabaseClient
from app.common.utils.config_manager import ConfigManager



class SupabaseSession:
    supabase = SupabaseClient.get_instance()

    @classmethod
    async def update_session_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the session data with user information based on the access token.

        Args:
            data (Dict[str, Any]): The session data containing the access token.

        Returns:
            Dict[str, Any]: The updated session data including the user's email and user ID.

        Raises:
            ValueError: If the access token is invalid or user cannot be found.
        """
        access_token = data["access_token"]
        token_data = await SupabaseAuth.verify_auth_token(access_token)

        # Extract email from token data
        email = token_data["user_email"]

        # Fetch the registered user ID based on the email
        user = await UserService.db_get(filters={"email": email}, fetch_one=True)

        # Add email and user_id to session data
        data["email"] = email
        data["user_id"] = user.id

        return data

    @classmethod
    async def get_session_by_device_code(cls, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Query the cli_sessions table for a session matching the given device code.

        Args:
            headers (Dict[str, str]): The headers containing the device code.

        Returns:
            Dict[str, Any]: A dictionary containing either:
                - 'jwt_token' (str): JWT token containing session data if found.
                - 'error' (str): Error message if an error occurred.
        """
        device_code = headers.get("X-Device-Code")
        if not device_code:
            raise ValueError("No device code found")

        response = cls.supabase.table("cli_sessions").select("*").eq("device_code", device_code).single().execute()
        session_data = response.data if response else None

        if not session_data:
            raise ValueError("No session data found")

        updated_session_data = await cls.update_session_data(session_data)

        # Encode the session data into a JWT token
        jwt_token = JWTHandler(signing_key=ConfigManager.config["JWT_SECRET_KEY"], algorithm="HS256").create_token(payload=updated_session_data)

        return {"jwt_token": jwt_token}
