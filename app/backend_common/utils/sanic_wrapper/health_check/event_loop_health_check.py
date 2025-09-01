import asyncio

from sanic.log import error_logger

from app.backend_common.utils.sanic_wrapper.common_utils import CONFIG
from app.backend_common.utils.sanic_wrapper.constants.errors import EVENT_LOOP_STARVED_ERROR
from app.backend_common.utils.sanic_wrapper.exceptions import BaseTorpedoException
from app.backend_common.utils.sanic_wrapper.health_check.health_check_strategy import HealthCheckStrategy


class EventLoopHealthCheck(HealthCheckStrategy):
    _health_check_config: dict = CONFIG.config.get("HEALTH_CHECK", {})
    sleep_duration = _health_check_config.get("EVENT_LOOP_CHECK_DELAY", 0.05)
    timeout_duration = _health_check_config.get("EVENT_LOOP_TIMEOUT_THRESHOLD", 0.1)

    async def check(self) -> str:
        try:
            await asyncio.wait_for(asyncio.sleep(self.sleep_duration), timeout=self.timeout_duration)
            return "healthy"
        except asyncio.TimeoutError:
            error_logger.error(EVENT_LOOP_STARVED_ERROR)
            raise BaseTorpedoException(EVENT_LOOP_STARVED_ERROR)
