from abc import ABC, abstractmethod


# Abstract Strategy for Health Check
class HealthCheckStrategy(ABC):
    @abstractmethod
    async def check(self) -> str:
        pass
