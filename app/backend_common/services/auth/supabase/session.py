import json
from typing import Any, Dict

from postgrest.exceptions import APIError

from app.backend_common.repository.users.user_repository import UserRepository
from app.backend_common.services.auth.session_encryption_service import (
    SessionEncryptionService,
)
from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.backend_common.services.auth.supabase.client import SupabaseClient
from app.common.constants.constants import AuthStatus


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

        if not token_data["valid"]:
            raise ValueError("Invalid access token")

        # Extract email from token data
        email = token_data["user_email"]

        # Fetch the registered user ID based on the email
        user = await UserRepository.db_get(filters={"email": email}, fetch_one=True)

        # Add email and user_id to session data
        data["email"] = email
        data["user_id"] = user.id

        return data

    @classmethod
    async def get_session_by_supabase_session_id(cls, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Query the external_sessions table for a session matching the given supabase session ID.

        Args:
            headers (Dict[str, str]): The headers containing the supabase session ID.

        Returns:
            Dict[str, Any]: A dictionary containing either:
                - 'encrypted_session_data' (str): encrypted_session_data if found.
                - 'error' (str): Error message if an error occurred.
        """
        supabase_session_id = headers.get("X-Supabase-Session-Id")
        if not supabase_session_id:
            raise ValueError("No supabase session ID found")

        try:
            response = (
                cls.supabase.table("external_sessions")
                .select("*")
                .eq("supabase_session_id", supabase_session_id)
                .single()
                .execute()
            )
            session_data = response.data if response else None

            if not session_data:
                raise ValueError("No session data found")

            updated_session_data = await cls.update_session_data(session_data)
            # need to convert to string for encryption service
            updated_session_data_string = json.dumps(updated_session_data)

            # Encrypting session data using session encryption service
            encrypted_session_data = SessionEncryptionService.encrypt(updated_session_data_string)

            return {"encrypted_session_data": encrypted_session_data, "status": AuthStatus.AUTHENTICATED.value}

        except APIError as e:
            if e.code == "PGRST116":
                return {"status": AuthStatus.PENDING.value}
            raise APIError
