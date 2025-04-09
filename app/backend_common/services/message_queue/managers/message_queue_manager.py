from abc import ABC, abstractmethod


class MessageQueueManager(ABC):
    @abstractmethod
    async def get_client(self, queue_name):
        raise NotImplementedError

    @abstractmethod
    async def publish(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def close(self):
        raise NotImplementedError

    @abstractmethod
    async def purge(self, message):
        raise NotImplementedError
