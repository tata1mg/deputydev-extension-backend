import os

from sanic import Sanic
from sanic.log import logger

from app.backend_common.utils.sanic_wrapper.config import SentryConfig
from app.backend_common.utils.sanic_wrapper.constants import ENV
from app.backend_common.utils.sanic_wrapper.integrations.elasticapm import init_apm
from app.backend_common.utils.sanic_wrapper.integrations.sentry import init_sentry


async def setup_sentry(app: Sanic) -> None:
    config = app.config.get("SENTRY")

    if not config:
        if not app.debug:
            logger.error("Sentry Config Not Found in Production!")
        else:
            logger.warning("Sentry Config Not Found! Skipping Integration")

        return

    sentry_config = SentryConfig(
        DSN=config.get("DSN"),
        ENVIRONMENT=config.get("ENVIRONMENT", "Local"),
        SERVICE_NAME=app.name,
        RELEASE_TAG=os.environ.get(ENV.RELEASE_TAG),
        CAPTURE_WARNING=config.get("CAPTURE_WARNING"),
    )

    await init_sentry(config=sentry_config)


# TODO: define a dataclass for apm config
def setup_apm(app: Sanic) -> None:
    apm_config = app.config.get("APM")

    if not apm_config:
        if not app.debug:
            logger.error("APM Config Not Found in Production!")
        else:
            logger.warning("APM Config Not Found! Skipping Integration")

        return

    apm_config["SERVICE_NAME"] = app.name
    apm_config["SERVICE_VERSION"] = os.environ.get(ENV.RELEASE_TAG)
    init_apm(app=app, config=apm_config)
