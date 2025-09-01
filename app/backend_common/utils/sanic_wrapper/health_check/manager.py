from typing import Dict

from app.backend_common.utils.sanic_wrapper.health_check import HealthCheckException, HealthCheckStrategy


class HealthCheckManager:
    def __init__(self, strategies: Dict[str, HealthCheckStrategy]):
        """Initialize the health check manager with strategies."""
        self._strategies = strategies

    async def execute_check(self, strategy_name: str) -> str:
        """Execute the health check for a given strategy."""
        strategy = self._strategies.get(strategy_name)
        if not strategy:
            raise HealthCheckException(f"Strategy '{strategy_name}' not found.")

        try:
            return await strategy.check()
        except HealthCheckException as e:
            # Capture the exception and re-raise it to be handled at a higher level
            error_message = f"Health check failed for {strategy_name}: {str(e)}"
            raise HealthCheckException(error_message)
