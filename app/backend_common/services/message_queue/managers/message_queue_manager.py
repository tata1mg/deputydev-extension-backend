from abc import ABC, abstractmethod
from typing import Any


class MessageQueueManager(ABC):
    @abstractmethod
    async def get_client(self, queue_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, **kwargs: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def purge(self, message: Any) -> None:
        raise NotImplementedError
