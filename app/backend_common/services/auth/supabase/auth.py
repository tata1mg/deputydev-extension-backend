import json
from datetime import datetime
from typing import Any, Dict, Tuple

import jwt
from gotrue.types import AuthResponse

from app.backend_common.caches.auth_token_grace_period_cache import AuthTokenGracePeriod
from app.backend_common.services.auth.session_encryption_service import (
    SessionEncryptionService,
)
from app.backend_common.services.auth.supabase.client import SupabaseClient
from app.backend_common.utils.sanic_wrapper import CONFIG


class SupabaseAuth:
    supabase = SupabaseClient.get_instance()

    @classmethod
    async def verify_auth_token(
        cls, access_token: str, use_grace_period: bool = False, enable_grace_period: bool = False
    ) -> Dict[str, Any]:
        """
        Validate a Supabase access token and check if it's expired.

        Args:
            access_token (str): The access token to validate.
            enable_grace_period(bool): If this is true, auth token is considered valid for current_time + grace_period
            use_grace_period(bool): If this is true only then grace_period is used

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'valid' (bool): Indicates if the token is valid.
                - 'message' (str): Status message explaining the validation result.
                - 'user_email' (Optional[str]): Email of the user if the token is valid, otherwise None.
                - 'user_name' (Optional[str]): Name of the user if the token is valid, otherwise None.

        """
        try:
            # Use the Supabase JWT secret key
            jwt_secret: str = CONFIG.config["SUPABASE"]["JWT_SECRET_KEY"]

            if not jwt_secret:
                return {"valid": False, "message": "JWT secret key is missing", "user_email": None, "user_name": None}

            # Decode and verify the JWT
            decoded_token = jwt.decode(
                access_token,
                key=jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": True, "require_exp": True, "verify_exp": True},
                audience="authenticated",
            )

            if use_grace_period and await cls.is_grace_period_available(access_token):
                return {
                    "valid": True,
                    "message": "Token is valid",
                    "user_email": decoded_token.get("email"),
                    "user_name": decoded_token.get("user_metadata").get("full_name"),
                }

            if enable_grace_period and decoded_token:
                await cls.add_grace_period(access_token, decoded_token)

            if decoded_token:
                return {
                    "valid": True,
                    "message": "Token is valid",
                    "user_email": decoded_token.get("email"),
                    "user_name": decoded_token.get("user_metadata").get("full_name"),
                }
            else:
                return {"valid": False, "message": "Token is invalid", "user_email": None, "user_name": None}

        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("The token has expired.")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token.")
        except Exception as e:  # noqa: BLE001
            raise Exception(f"Token validation failed: {str(e)}")

    @classmethod
    async def is_grace_period_available(cls, access_token: str) -> bool:
        is_token_present: Any = await AuthTokenGracePeriod.get(access_token)
        return bool(is_token_present)

    @classmethod
    async def add_grace_period(cls, access_token: str, decoded_token: Dict[str, Any]) -> None:
        exp_timestamp = decoded_token.get("exp")
        if exp_timestamp is not None:
            await AuthTokenGracePeriod.set(access_token, 1)

    @classmethod
    async def extract_and_validate_token(cls, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract the access token from the headers, validate its format, and verify it.

        Args:
            headers (Dict): The headers containing the access token.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'valid' (bool): Indicates if the token is valid.
                - 'message' (str): Status message explaining the validation result.
                - 'user_email' (Optional[str]): Email of the user if the token is valid, otherwise None.
                - 'user_name' (Optional[str]): Name of the user if the token is valid, otherwise None.
        """
        if "Authorization" not in headers:
            return {"valid": False, "message": "Authorization header missing", "user_email": None, "user_name": None}

        auth_header = headers["Authorization"]
        access_token = auth_header.split(" ")[1]
        if not access_token:
            return {"valid": False, "message": "Access token missing", "user_email": None, "user_name": None}

        # Call the verify_auth_token method with the access token
        return await cls.verify_auth_token(access_token)

    @classmethod
    async def refresh_session(cls, session_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Refreshes the user session by obtaining new access and refresh tokens.

        This method calls the Supabase authentication service to refresh the session
        using the provided refresh token. It updates the session data with the new
        tokens and encrypts the session data before returning it.

        Args:
            session_data (Dict[str, Any]): A dictionary containing the session data,
                including the refresh token.

        Returns:
            Tuple[str, str, str]: A tuple containing the encrypted session data,
                the user's email, and the user's full name.

        Raises:
            Exception: If the refresh operation fails or if there is an error during
                the process.
        """
        try:
            # Call the Supabase auth refresh method with the provided refresh token
            response: AuthResponse = cls.supabase.auth.refresh_session(session_data.get("refresh_token"))

            if not response.session or not response.user:
                raise Exception("Failed to refresh tokens.")

            # extracting email and user name
            email = response.user.email
            user_name: str = response.user.user_metadata["full_name"]

            if not email or not user_name:
                raise Exception("User email or name is missing in the response.")

            # update the session data with the refreshed access and refresh tokens
            session_data["access_token"] = response.session.access_token
            session_data["refresh_token"] = response.session.refresh_token
            session_data["token_updated_at"] = str(datetime.now())
            # return the refreshed session data
            encrypted_session_data = SessionEncryptionService.encrypt(json.dumps(session_data))
            return encrypted_session_data, email, user_name
        except Exception as e:  # noqa: BLE001
            # Handle exceptions (e.g., log the error)
            raise Exception(f"Error refreshing session: {str(e)}")
