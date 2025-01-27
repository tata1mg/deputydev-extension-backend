from datetime import datetime, timezone
from typing import Any, Dict

import jwt

from app.backend_common.services.auth.supabase.client import SupabaseClient


class SupabaseAuth:
    supabase = SupabaseClient.get_instance()

    @classmethod
    async def verify_auth_token(cls, access_token: str) -> Dict[str, Any]:
        """
        Validate a Supabase access token and check if it's expired.

        Args:
            access_token (str): The access token to validate.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'valid' (bool): Indicates if the token is valid.
                - 'message' (str): Status message explaining the validation result.
                - 'user_email' (Optional[str]): Email of the user if the token is valid, otherwise None.
                - 'user_name' (Optional[str]): Name of the user if the token is valid, otherwise None.
        """
        try:
            # Decode the JWT token without verification to check expiration
            decoded_token = jwt.decode(access_token, options={"verify_signature": False})

            # Check token expiration
            exp_timestamp = decoded_token.get("exp")
            if exp_timestamp is not None:
                current_time = int(datetime.now(timezone.utc).timestamp())
                if current_time > exp_timestamp:
                    return {"valid": False, "message": "Token has expired", "user_email": None, "user_name": None}

            # Verify token with Supabase
            user_response = cls.supabase.auth.get_user(access_token)
            if user_response.user:
                return {
                    "valid": True,
                    "message": "Token is valid",
                    "user_email": user_response.user.email,
                    "user_name": user_response.user.user_metadata["full_name"],
                }
            else:
                return {"valid": False, "message": "Token is invalid", "user_email": None, "user_name": None}

        except jwt.ExpiredSignatureError:
            return {"valid": False, "message": "Token has expired", "user_email": None, "user_name": None}
        except jwt.InvalidTokenError:
            return {"valid": False, "message": "Invalid token format", "user_email": None, "user_name": None}
        except Exception as e:
            return {
                "valid": False,
                "message": f"Token validation failed: {str(e)}",
                "user_email": None,
                "user_name": None,
            }

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
