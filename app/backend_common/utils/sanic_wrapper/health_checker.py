from app.backend_common.utils.sanic_wrapper.constants.constants import HEALTHY_STATUS
from app.backend_common.utils.sanic_wrapper.constants.errors import (
    EVENT_LOOP_STARVED_ERROR,
    SERVICE_RESPONSE_HEALTH_CHECK_FAILED,
)
from app.backend_common.utils.sanic_wrapper.health_check import (
    EventLoopHealthCheck,
    ServiceResponseHealthCheck,
)
from app.backend_common.utils.sanic_wrapper.health_check.manager import HealthCheckManager

# Instantiate strategies
event_loop_health_check = EventLoopHealthCheck()
service_response_health_check = ServiceResponseHealthCheck()

# Create a health check manager with both strategies
health_manager = HealthCheckManager(
    {
        "event_loop": event_loop_health_check,
        "service_response": service_response_health_check,
    }
)


class HealthChecker:
    """Handles all health check operations."""

    @staticmethod
    async def run_health_checks():
        """Executes health checks and returns (status, error_message)."""
        loop_status = await health_manager.execute_check("event_loop")
        if loop_status != HEALTHY_STATUS:
            return loop_status, EVENT_LOOP_STARVED_ERROR

        service_status = await health_manager.execute_check("service_response")
        if service_status != HEALTHY_STATUS:
            return service_status, SERVICE_RESPONSE_HEALTH_CHECK_FAILED

        return HEALTHY_STATUS, None
