"""
This module integrates Sentry SDK with the application for error reporting.
"""

import logging
from contextlib import suppress

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.backend_common.utils.sanic_wrapper.config import SentryConfig


async def init_sentry(config: SentryConfig) -> None:
    """Initializes Sentry SDK with provided configuration.

    Warning:
        We do NOT use official Sanic integration `SanicIntegration` for sentry.
        This is intentional. Please discuss before adding the integration.

    Args:
        config (SentryConfig): Configuration settings for Sentry.
    """
    sentry_sdk.set_tag("service_name", config.SERVICE_NAME)

    event_level = logging.WARNING if config.CAPTURE_WARNING else logging.ERROR

    integrations = [
        AsyncioIntegration(),  # err reporting bg tasks
        LoggingIntegration(event_level=event_level),
    ]

    sentry_sdk.init(
        dsn=config.DSN,
        environment=config.ENVIRONMENT,
        release=config.RELEASE_TAG,
        integrations=integrations,
        before_send=before_send,
    )

    # patch hub exit
    sentry_sdk.integrations.sanic._hub_exit = _hub_exit_modified


def before_send(event, hint):
    """Custom function to modify Sentry events before they are sent.

    Args:
        event (dict): The event data that will be sent to Sentry.
        hint (dict): Additional information about the event.

    Returns:
        dict or None: The modified event data, or None to discard the event.
    """
    if "exc_info" in hint:
        exc_type, exc_value, traceback = hint["exc_info"]
        if hasattr(exc_value, "sentry_raise") and not exc_value.sentry_raise:
            return None
    return event


async def _hub_exit_modified(request, **_):
    """Modified hub exit to safely exit Sentry's hub context for a given request.

    This is a patch required due to this issue: https://github.com/getsentry/sentry-python/issues/1290
    """
    with suppress(IndexError):
        request.ctx._sentry_hub.__exit__(None, None, None)
