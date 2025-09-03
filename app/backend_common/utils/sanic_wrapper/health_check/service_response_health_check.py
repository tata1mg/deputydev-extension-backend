from sanic.log import error_logger

from app.backend_common.utils.sanic_wrapper.clients import SanicClient
from app.backend_common.utils.sanic_wrapper.constants.errors import SERVICE_RESPONSE_HEALTH_CHECK_FAILED
from app.backend_common.utils.sanic_wrapper.exceptions import BaseSanicException
from app.backend_common.utils.sanic_wrapper.health_check.health_check_strategy import HealthCheckStrategy


class ServiceResponseHealthCheck(HealthCheckStrategy):
    async def check(self) -> str:
        try:
            result = await SanicClient.get(path="/ping", purge_response_keys=True)
            if result.status != 200:
                error_logger.error(SERVICE_RESPONSE_HEALTH_CHECK_FAILED)
                raise BaseSanicException(SERVICE_RESPONSE_HEALTH_CHECK_FAILED)
            return "healthy"
        except Exception as e:
            error_logger.error(f"Service response health check failed: {e}")
            raise BaseSanicException(SERVICE_RESPONSE_HEALTH_CHECK_FAILED)
