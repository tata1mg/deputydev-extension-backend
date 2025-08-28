from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAuth(ABC):
    @abstractmethod
    async def extract_and_verify_token(self, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("This extract_and_verify_token method must be implemented in the child class")
