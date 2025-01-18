
import pdb
from typing import Dict, Optional, Tuple, Any
import jwt
from datetime import datetime, timezone
from app.backend_common.services.supabase.client import supabase

class SupabaseAuth:
    def __init__(self):
        self.supabase = supabase

    @classmethod
    async def verify_auth_token(cls, access_token: str) -> Dict[str, Any]:
        """
        Validate a Supabase access token and check if it's expired.

        Args:
            access_token (str): The access token to validate.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'valid': Boolean indicating if the token is valid
                - 'message': Status message explaining the validation result
                - 'user_response': UserResponse object if token is valid, None otherwise
        """
        try:
            pdb.set_trace()
            # Decode the JWT token without verification to check expiration
            decoded_token = jwt.decode(access_token, options={"verify_signature": False})

            # Check token expiration
            exp_timestamp = decoded_token.get('exp')
            if exp_timestamp is not None:
                current_time = int(datetime.now(timezone.utc).timestamp())
                if current_time > exp_timestamp:
                    return {
                        'valid': False,
                        'message': "Token has expired",
                    }

            # Verify token with Supabase
            user_response = supabase.auth.get_user(access_token)
            # print(user_response)
            if user_response.user:
                return {
                    'valid': True,
                    'message': "Token is valid"
                }
            else:
                return {
                    'valid': False,
                    'message': "Token is invalid",
                }

        except jwt.ExpiredSignatureError:
            return {
                'valid': False,
                'message': "Token has expired",
            }
        except jwt.InvalidTokenError:
            return {
                'valid': False,
                'message': "Invalid token format",
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f"Token validation failed: {str(e)}",
            }

    @classmethod
    async def extract_and_validate_token(cls, headers: Dict) -> Dict[str, Any]:
        """
        Extract the access token from the headers, validate its format, and verify it.

        Args:
            headers (Dict): The headers containing the access token.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'valid': Boolean indicating if the token is valid
                - 'message': Status message explaining the validation result
                - 'user_response': UserResponse object if token is valid, None otherwise
        """
        if 'Authorization' not in headers:
            return {
                'valid': False,
                'message': "Authorization header missing",
                'user_response': None
            }

        auth_header = headers['Authorization']
        access_token = auth_header.split(' ')[1]
        if not access_token:
            return {
                'valid': False,
                'message': "Access token missing",
                'user_response': None
            }

        # Call the verify_auth_token method with the access token
        return await cls.verify_auth_token(access_token)