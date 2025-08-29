from abc import ABC, abstractmethod
from typing import Any, Dict

from torpedo import Request


class BaseAuth(ABC):
    @abstractmethod
    async def get_auth_session(self, headers: Dict[str, str]) -> Dict[str, Any]:
        raise NotImplementedError("This get_auth_session method must be implemented in the child class")

    @abstractmethod
    async def extract_and_verify_token(self, request: Request) -> Dict[str, Any]:
        raise NotImplementedError("This extract_and_verify_token method must be implemented in the child class")
