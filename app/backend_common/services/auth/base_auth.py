from abc import ABC, abstractmethod
from typing import Dict

from torpedo import Request

from app.backend_common.utils.dataclasses.main import AuthSessionData


class BaseAuth(ABC):
    """Abstract base class for authentication services.

    This class defines the interface that all authentication service implementations must follow.
    It provides abstract methods for handling authentication sessions and token verification.

    Subclasses must implement the following methods:
        - get_auth_session: Retrieve authentication session data from headers
        - extract_and_verify_token: Extract and validate authentication tokens from requests
    """

    @abstractmethod
    async def get_auth_session(self, headers: Dict[str, str]) -> AuthSessionData:
        """Retrieve and validate authentication session data from request headers.

        Args:
            headers: Dictionary containing HTTP headers from the request

        Returns:
            AuthSessionData: An instance containing the authenticated session information

        Raises:
            AuthenticationError: If the session cannot be authenticated
        """
        raise NotImplementedError("This get_auth_session method must be implemented in the child class")

    @abstractmethod
    async def extract_and_verify_token(self, request: Request) -> AuthSessionData:
        """Extract and validate an authentication token from the request.

        Args:
            request: The incoming request containing the authentication token

        Returns:
            AuthSessionData: An instance containing the authenticated session information

        Raises:
            AuthenticationError: If the token is invalid or expired
        """
        raise NotImplementedError("This extract_and_verify_token method must be implemented in the child class")
