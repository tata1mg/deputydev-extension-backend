from typing import Any, Dict
from datetime import datetime, timezone

import jwt


class JWTHandler:
    """
    A class to generate and verify JWT tokens.
    """

    def __init__(self, signing_key: str, algorithm="HS256"):
        """
        Initialize the JWTHandler.

        Args:
            secret_key (str): The secret key for signing tokens.
            algorithm (str): The algorithm to use for signing (default is HS256).
            expiration_minutes (int): Token expiration time in minutes (default is 30).
        """
        self.secret_key = signing_key
        self.algorithm = algorithm

    def create_token(self, payload) -> str:
        """
        Create a JWT token with the given payload.

        Args:
            payload (dict): The payload to include in the token.

        Returns:
            str: The generated JWT token.
        """
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a JWT token and return its payload.

        Args:
            token (str): The JWT token to verify.

        Returns:
            dict: The decoded payload if the token is valid.

        Raises:
            jwt.ExpiredSignatureError: If the token has expired.
            jwt.InvalidTokenError: If the token is invalid.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("The token has expired.")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token.")

    def verify_token_without_signature_verification(token: str) -> bool:
        """Verifies the JWT token without signature verification and checks for expiration.

        Args:
            token (str): The JWT token to verify.

        Returns:
            bool: True if the token is valid and not expired, False otherwise.
        """
        try:
            # Decode the JWT token without verifying the signature
            decoded_token = jwt.decode(token, options={"verify_signature": False})

            # Check token expiration
            exp_timestamp = decoded_token.get("exp")
            if exp_timestamp is not None:
                current_time = int(datetime.now(timezone.utc).timestamp())
                if current_time > exp_timestamp:
                    return False

            return True

        except jwt.DecodeError:
            return False
