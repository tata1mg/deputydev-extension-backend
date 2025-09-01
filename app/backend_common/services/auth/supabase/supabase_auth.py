import json
from datetime import datetime
from typing import Any, Dict

import jwt
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.auth import AuthStatus
from gotrue.types import AuthResponse
from jwt import ExpiredSignatureError, InvalidTokenError
from postgrest.exceptions import APIError
from torpedo import Request
from torpedo.exceptions import BadRequestException

from app.backend_common.caches.auth_token_grace_period_cache import AuthTokenGracePeriod
from app.backend_common.repository.users.user_repository import UserRepository
from app.backend_common.services.auth.base_auth import BaseAuth
from app.backend_common.services.auth.session_encryption_service import SessionEncryptionService
from app.backend_common.services.auth.supabase.client import SupabaseClient
from app.backend_common.utils.dataclasses.main import AuthSessionData, AuthTokenData, RefreshedSessionData


class SupabaseAuth(BaseAuth):
    """Implementation of BaseAuth using Supabase for authentication and session management.

    This class handles user authentication, session management, and token validation
    using Supabase as the authentication provider. It implements the abstract methods
    defined in the BaseAuth class.
    """

    supabase = SupabaseClient.get_instance()

    async def update_session_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update session data with user information from the access token.

        Args:
            data: Dictionary containing session data including 'access_token'.

        Returns:
            Updated session data with additional user information (email, user_name, user_id).

        Raises:
            ValueError: If the access token is invalid or user information is missing.
        """
        access_token = data["access_token"]
        token_data: AuthTokenData = await self.verify_auth_token(access_token)

        if not token_data.valid:
            raise ValueError("Invalid access token")

        # Check for user_email and user_name in token_data
        email = token_data.user_email
        user_name = token_data.user_name

        # Fetch the registered user ID based on the email
        user = await UserRepository.db_get(filters={"email": email}, fetch_one=True)

        # Add email and user_id to session data
        data["email"] = email
        data["user_name"] = user_name
        data["user_id"] = user.id

        return data

    async def get_auth_session(self, headers: Dict[str, str]) -> AuthSessionData:
        """Retrieve and validate an authentication session from Supabase.

        Args:
            headers: HTTP headers containing 'X-Unique-Session-Id' for session lookup.

        Returns:
            AuthSessionData containing encrypted session data and user information.

        Raises:
            ValueError: If session ID is missing or no session data is found.
            APIError: If there's an error communicating with Supabase.
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

            return AuthSessionData(
                encrypted_session_data=encrypted_session_data,
                user_email=updated_session_data["email"],
                user_name=updated_session_data["user_name"],
                status=AuthStatus.AUTHENTICATED,
            )

        except APIError as e:
            if e.code == "PGRST116":
                return AuthSessionData(status=AuthStatus.PENDING)
            raise e

    async def verify_auth_token(
        self, access_token: str, use_grace_period: bool = False, enable_grace_period: bool = False
    ) -> AuthTokenData:
        """Validate a Supabase JWT access token.

        Args:
            access_token: The JWT token to validate.
            use_grace_period: If True, allows token validation during grace period.
            enable_grace_period: If True, enables grace period for token expiration.

        Returns:
            AuthTokenData containing validation result and user information.

        Raises:
            ExpiredSignatureError: If token has expired and no grace period is available.
            InvalidTokenError: If token is malformed or invalid.
            Exception: For other validation errors.
        """
        try:
            # Use the Supabase JWT secret key
            jwt_secret: str = ConfigManager.configs["SUPABASE"]["JWT_SECRET_KEY"]

            if not jwt_secret:
                return AuthTokenData(
                    valid=False,
                    message="JWT secret key is missing",
                )

            # Decode and verify the JWT
            decoded_token = jwt.decode(
                access_token,
                key=jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": True, "require_exp": True, "verify_exp": True},
                audience="authenticated",
            )

            if use_grace_period and await self.is_grace_period_available(access_token):
                return AuthTokenData(
                    valid=True,
                    message="Token is valid",
                    user_email=decoded_token.get("email"),
                    user_name=decoded_token.get("user_metadata").get("full_name"),
                )

            if enable_grace_period and decoded_token:
                await self.add_grace_period(access_token, decoded_token)

            if decoded_token:
                return AuthTokenData(
                    valid=True,
                    message="Token is valid",
                    user_email=decoded_token.get("email"),
                    user_name=decoded_token.get("user_metadata").get("full_name"),
                )
            return AuthTokenData(valid=False, message="Token is invalid")

        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("The token has expired.")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token.")
        except Exception as e:  # noqa: BLE001
            raise Exception(f"Token validation failed: {str(e)}")

    async def is_grace_period_available(self, access_token: str) -> bool:
        """Check if a grace period is available for the given access token.

        Args:
            access_token: The token to check grace period for.

        Returns:
            bool: True if grace period is available, False otherwise.
        """
        is_token_present: Any = await AuthTokenGracePeriod.get(access_token)
        return bool(is_token_present)

    async def add_grace_period(self, access_token: str, decoded_token: Dict[str, Any]) -> None:
        """Add a grace period for an access token.

        Args:
            access_token: The token to add grace period for.
            decoded_token: Decoded JWT token data.
        """
        exp_timestamp = decoded_token.get("exp")
        if exp_timestamp is not None:
            await AuthTokenGracePeriod.set(access_token, 1)

    async def refresh_session(self, session_data: Dict[str, Any]) -> RefreshedSessionData:
        """Refresh an expired session using the refresh token.

        Args:
            session_data: Current session data containing refresh token.

        Returns:
            Tuple containing (encrypted_session_data, email, user_name).

        Raises:
            Exception: If session refresh fails or user data is missing.
        """
        try:
            response: AuthResponse = self.supabase.auth.refresh_session(session_data.get("refresh_token"))

            if not response.session or not response.user:
                raise Exception("Failed to refresh tokens.")

            # extracting email and user name
            user_email = response.user.email
            user_name: str = response.user.user_metadata["full_name"]

            if not user_email or not user_name:
                raise Exception("User email or name is missing in the response.")

            # update the session data with the refreshed access and refresh tokens
            session_data["access_token"] = response.session.access_token
            session_data["refresh_token"] = response.session.refresh_token
            session_data["token_updated_at"] = str(datetime.now())
            # return the refreshed session data
            refreshed_session = SessionEncryptionService.encrypt(json.dumps(session_data))
            return RefreshedSessionData(refreshed_session=refreshed_session, user_email=user_email, user_name=user_name)
        except Exception as e:  # noqa: BLE001
            raise Exception(f"Error refreshing session: {str(e)}")

    async def validate_session(
        self, encrypted_session_data: str, use_grace_period: bool = False, enable_grace_period: bool = False
    ) -> AuthSessionData:
        """Validate an encrypted session and check token validity.

        Args:
            encrypted_session_data: Encrypted session data string.
            use_grace_period: If True, allows validation during grace period.
            enable_grace_period: If True, enables grace period for token expiration.

        Returns:
            AuthSessionData with validation status and user information.

        Raises:
            Various exceptions from decryption and validation processes.
        """
        session_data: Dict[str, Any] = {}
        try:
            # first decrypt the encrypted session data using session encryption service
            session_data_string = SessionEncryptionService.decrypt(encrypted_session_data)
            # convert back to json object
            session_data = json.loads(session_data_string)
            # extract supabase access token
            access_token: str = session_data.get("access_token") or ""

            token_data: AuthTokenData = await self.verify_auth_token(
                access_token, use_grace_period=use_grace_period, enable_grace_period=enable_grace_period
            )

            if not token_data.valid:
                return AuthSessionData(status=AuthStatus.NOT_VERIFIED)

            return AuthSessionData(
                status=AuthStatus.VERIFIED,
                user_email=token_data.user_email,
                user_name=token_data.user_name,
            )

        except ExpiredSignatureError:
            # refresh the current session
            try:
                refreshed_session_data: RefreshedSessionData = await self.refresh_session(session_data)
                return AuthSessionData(
                    status=AuthStatus.EXPIRED,
                    encrypted_session_data=refreshed_session_data.refreshed_session,
                    user_email=refreshed_session_data.user_email,
                    user_name=refreshed_session_data.user_name,
                )
            except Exception as _ex:  # noqa: BLE001
                return AuthSessionData(
                    status=AuthStatus.NOT_VERIFIED,
                    error_message=str(_ex),
                )

        except InvalidTokenError:
            return AuthSessionData(
                status=AuthStatus.NOT_VERIFIED,
                error_message="Invalid token format.",
            )
        except Exception as _ex:  # noqa: BLE001
            return AuthSessionData(
                status=AuthStatus.NOT_VERIFIED,
                error_message=str(_ex),
            )

    async def extract_and_verify_token(self, request: Request) -> AuthSessionData:
        """Extract and verify authentication token from the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            AuthSessionData with verification results.

        Raises:
            BadRequestException: If Authorization header is missing.
        """
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
        verification_result = await self.validate_session(
            encrypted_session_data, use_grace_period=use_grace_period, enable_grace_period=enable_grace_period
        )
        return verification_result
