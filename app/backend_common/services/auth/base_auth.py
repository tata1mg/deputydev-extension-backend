from abc import ABC, abstractmethod
from typing import Dict

from torpedo import Request

from app.backend_common.utils.dataclasses.main import AuthSessionData


class BaseAuth(ABC):
    @abstractmethod
    async def get_auth_session(self, headers: Dict[str, str]) -> AuthSessionData:
        raise NotImplementedError("This get_auth_session method must be implemented in the child class")

    @abstractmethod
    async def extract_and_verify_token(self, request: Request) -> AuthSessionData:
        raise NotImplementedError("This extract_and_verify_token method must be implemented in the child class")
