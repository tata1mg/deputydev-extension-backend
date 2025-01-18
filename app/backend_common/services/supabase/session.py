from typing import Dict, Optional, Tuple, Any
from postgrest.exceptions import APIError
from app.common.services.authentication.jwt import JWTHandler
from .client import supabase
from torpedo import CONFIG

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
        device_code = headers.get('X-Device-Code')
        if not device_code:
            return {
                'error': {
                    'message': 'Device code missing in headers',
                    'code': 'MISSING_DEVICE_CODE',
                    'status': 400
                }
            }

        try:
            response = supabase.table('cli_sessions').select('*').eq('device_code', device_code).single().execute()
            data = response.data if response else None

            if not data:
                return {
                    'error': {
                        'message': 'No session data found',
                        'code': 'NO_DATA',
                        'status': 404
                    }
                }

            # Encode the session data into a JWT token
            jwt_token = JWTHandler(signing_key=JWT_SECRET, algorithm='HS256').create_token(payload=data)

            return {
                'jwt_token': jwt_token
            }

        except APIError as e:
            return {
                'error': {
                    'message': str(e),
                    'code': getattr(e, 'code', 'UNKNOWN_ERROR'),
                    'status': 500
                }
            }