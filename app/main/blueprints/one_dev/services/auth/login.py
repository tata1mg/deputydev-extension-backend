import json
from typing import Any, Dict

from jwt import ExpiredSignatureError, InvalidTokenError

from app.backend_common.services.auth.session_encryption_service import (
    SessionEncryptionService,
)
from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from deputydev_core.utils.constants.auth import AuthStatus


class Login:
    @classmethod
    async def verify_auth_token(cls, encrypted_session_data: str, enable_grace_period: bool = False) -> Dict[str, Any]:
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
            access_token = session_data.get("access_token")
            response = await SupabaseAuth.verify_auth_token(access_token, enable_grace_period=enable_grace_period)
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
                refresh_session_data, email, user_name = await SupabaseAuth.refresh_session(session_data)
                await cls.verify_auth_token(refresh_session_data, enable_grace_period)
                return {
                    "status": AuthStatus.EXPIRED.value,
                    "encrypted_session_data": refresh_session_data,
                    "user_email": email,
                    "user_name": user_name,
                }
            except Exception as _ex:
                return {
                    "status": AuthStatus.NOT_VERIFIED.value,
                    "error_message": str(_ex),
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
