"""Torpedo Internal Routes."""

from sanic import Blueprint, response

from app.backend_common.utils.sanic_wrapper.constants.constants import HEALTHY_STATUS, UNHEALTHY_STATUS
from app.backend_common.utils.sanic_wrapper.health_check.health_checker import HealthChecker

health_bp = Blueprint("__torpedo__health")


@health_bp.get("/ping")
async def ping(_):
    """Healthcheck endpoint for Liveness and Readiness Probe.
    Note:
        Sanic provides health check endpoint via `sanic-ext`
        but this is, for legacy reasons, uniform across all services.
    """
    return response.json({"ping": "pong"})


@health_bp.get("/health/status")
async def health_status(_):
    try:
        status, error = await HealthChecker.run_health_checks()
        if error:
            return response.json({"status": status, "error": error}, status=500)

        return response.json({"status": HEALTHY_STATUS})

    except Exception as e:
        return response.json({"status": UNHEALTHY_STATUS, "error": str(e)}, status=500)
