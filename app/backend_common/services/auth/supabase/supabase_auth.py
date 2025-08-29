import json
from datetime import datetime
from typing import Any, Dict, Tuple

import jwt
from deputydev_core.utils.constants.auth import AuthStatus
from gotrue.types import AuthResponse
from jwt import ExpiredSignatureError, InvalidTokenError
from postgrest.exceptions import APIError
from torpedo import CONFIG, Request
from torpedo.exceptions import BadRequestException

from app.backend_common.caches.auth_token_grace_period_cache import AuthTokenGracePeriod
from app.backend_common.repository.users.user_repository import UserRepository
from app.backend_common.services.auth.base_auth import BaseAuth
from app.backend_common.services.auth.session_encryption_service import SessionEncryptionService
from app.backend_common.services.auth.supabase.client import SupabaseClient


class SupabaseAuth(BaseAuth):
    supabase = SupabaseClient.get_instance()

    async def update_session_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the session data with user information based on the access token.

        Args:
            data (Dict[str, Any]): The session data containing the access token.

        Returns:
            Dict[str, Any]: The updated session data including the user's email and user ID.

        Raises:
            ValueError: If the access token is invalid, user cannot be found, or user information is missing.
        """
        access_token = data["access_token"]
        token_data = await self.verify_auth_token(access_token)

        if not token_data["valid"]:
            raise ValueError("Invalid access token")

        # Check for user_email and user_name in token_data
        email = token_data["user_email"]
        user_name = token_data["user_name"]

        # Fetch the registered user ID based on the email
        user = await UserRepository.db_get(filters={"email": email}, fetch_one=True)

        # Add email and user_id to session data
        data["email"] = email
        data["user_name"] = user_name
        data["user_id"] = user.id

        return data

    async def get_auth_session(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Query the external_sessions table for a session matching the given Supabase session ID.

        Args:
            headers (Dict[str, str]): The headers containing the Supabase session ID.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'encrypted_session_data' (str): The encrypted session data if found.
                - 'user_email' (str): The email of the user associated with the session.
                - 'user_name' (str): The name of the user associated with the session.
                - 'status' (str): The authentication status, indicating if the user is authenticated or pending.

        Raises:
            ValueError: If no Supabase session ID is found or if no session data is found.
            APIError: If there is an error during the API call.
        """
        unique_session_id = headers.get("X-Unique-Session-Id")
        if not unique_session_id:
            raise ValueError("No unique session ID found")
        supabase_client = SupabaseClient.get_public_instance()
        try:
            response = (
                supabase_client.table("external_sessions")
                .select("*")
                .eq("supabase_session_id", unique_session_id)
                .single()
                .execute()
            )
            session_data: Dict[str, Any] = response.data if response else None

            if not session_data:
                raise ValueError("No session data found")

            updated_session_data = await self.update_session_data(session_data)
            # need to convert to string for encryption service
            updated_session_data_string = json.dumps(updated_session_data)

            # Encrypting session data using session encryption service
            encrypted_session_data = SessionEncryptionService.encrypt(updated_session_data_string)

            return {
                "encrypted_session_data": encrypted_session_data,
                "user_email": updated_session_data["email"],
                "user_name": updated_session_data["user_name"],
                "status": AuthStatus.AUTHENTICATED.value,
            }

        except APIError as e:
            if e.code == "PGRST116":
                return {"status": AuthStatus.PENDING.value}
            raise e

    async def verify_auth_token(
        self, access_token: str, use_grace_period: bool = False, enable_grace_period: bool = False
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

            if use_grace_period and await self.is_grace_period_available(access_token):
                return {
                    "valid": True,
                    "message": "Token is valid",
                    "user_email": decoded_token.get("email"),
                    "user_name": decoded_token.get("user_metadata").get("full_name"),
                }

            if enable_grace_period and decoded_token:
                await self.add_grace_period(access_token, decoded_token)

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

    async def is_grace_period_available(self, access_token: str) -> bool:
        is_token_present: Any = await AuthTokenGracePeriod.get(access_token)
        return bool(is_token_present)

    async def add_grace_period(self, access_token: str, decoded_token: Dict[str, Any]) -> None:
        exp_timestamp = decoded_token.get("exp")
        if exp_timestamp is not None:
            await AuthTokenGracePeriod.set(access_token, 1)

    async def refresh_session(self, session_data: Dict[str, Any]) -> Tuple[str, str, str]:
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
            response: AuthResponse = self.supabase.auth.refresh_session(session_data.get("refresh_token"))

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

    async def validate_session(
        self, encrypted_session_data: str, use_grace_period: bool = False, enable_grace_period: bool = False
    ) -> Dict[str, Any]:
        session_data: Dict[str, Any] = {}
        """
        Verifies the authenticity of the provided encrypted session data by decrypting it
        and checking the validity of the associated access token.

        Args:
            encrypted_session_data (str): The encrypted session data containing the access token.
            enable_grace_period (bool): A flag indicating whether to allow a grace period for token expiry.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'status' (str): The verification status, which can be:
                    - 'VERIFIED': If the token is valid.
                    - 'NOT_VERIFIED': If the token is invalid or not verified.
                    - 'EXPIRED': If the token has expired and a new session is created.
                - 'user_email' (str): The email of the user associated with the session (if verified).
                - 'user_name' (str): The name of the user associated with the session (if verified).
                - 'encrypted_session_data' (str): The new encrypted session data if the token has expired.
                - 'error_message' (str): An error message if the verification fails.

        Raises:
            ExpiredSignatureError: If the access token has expired.
            InvalidTokenError: If the token format is invalid.
            Exception: If any other error occurs during the verification process.
        """
        try:
            # first decrypt the encrypted session data using session encryption service
            session_data_string = SessionEncryptionService.decrypt(encrypted_session_data)
            # convert back to json object
            session_data = json.loads(session_data_string)
            # extract supabase access token
            access_token: str = session_data.get("access_token") or ""
            response = await self.verify_auth_token(
                access_token, use_grace_period=use_grace_period, enable_grace_period=enable_grace_period
            )
            if not response["valid"]:
                return {"status": AuthStatus.NOT_VERIFIED.value}
            return {
                "status": AuthStatus.VERIFIED.value,
                "user_email": response["user_email"],
                "user_name": response["user_name"],
            }
        except ExpiredSignatureError:
            # refresh the current session
            try:
                refresh_session_data, email, user_name = await self.refresh_session(session_data)
                return {
                    "status": AuthStatus.EXPIRED.value,
                    "encrypted_session_data": refresh_session_data,
                    "user_email": email,
                    "user_name": user_name,
                }
            except Exception as _ex:  # noqa: BLE001
                return {
                    "status": AuthStatus.NOT_VERIFIED.value,
                    "error_message": str(_ex),
                }
        except InvalidTokenError:
            return {
                "status": AuthStatus.NOT_VERIFIED.value,
                "error_message": "Invalid token format.",
            }
        except Exception as _ex:  # noqa: BLE001
            return {
                "status": AuthStatus.NOT_VERIFIED.value,
                "error_message": str(_ex),
            }

    async def extract_and_verify_token(self, request: Request) -> Dict[str, Any]:
        use_grace_period: bool = False
        enable_grace_period: bool = False
        payload: Dict[str, Any] = {}

        authorization_header: str = request.headers.get("Authorization")
        if not authorization_header:
            raise BadRequestException("Authorization header is missing")

        try:
            payload = request.custom_json() if request.method == "POST" else request.request_params()
            use_grace_period = payload.get("use_grace_period") or False
            enable_grace_period = payload.get("enable_grace_period") or False
        except Exception:  # noqa: BLE001
            pass

        # decode encrypted session data and get the supabase access token
        encrypted_session_data = authorization_header.split(" ")[1]
        verfication_result = await self.validate_session(
            encrypted_session_data, use_grace_period=use_grace_period, enable_grace_period=enable_grace_period
        )
        return verfication_result
