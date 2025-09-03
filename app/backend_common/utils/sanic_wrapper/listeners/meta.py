import time

from sanic import Sanic
from sanic.log import logger


def add_service_started(app: Sanic):
    """Add `service_started` to app context."""

    app.ctx.service_started = int(time.perf_counter() * 1000)


def log_meta(app: Sanic):
    """Log service meta info.."""

    # prepare service meta info
    service_init_duration = int(time.perf_counter() * 1000) - app.ctx.service_started
    service_meta_info = {
        "service_init_duration": service_init_duration,
        "workers_count": app.config.get("WORKERS"),
        "debug_mode": app.debug,
    }

    logger.info("Service Meta Info", extra=service_meta_info)
