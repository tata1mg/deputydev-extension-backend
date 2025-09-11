from typing import Any

from sanic import Sanic

from app.backend_common.utils.redis_wrapper.registry import cache_registry
from app.backend_common.utils.sanic_wrapper.constants import ListenerEventTypes
from app.backend_common.utils.tortoise_wrapper import TortoiseWrapper
from app.main.blueprints.one_dev.services.kafka.analytics_events.analytics_event_subscriber import (
    AnalyticsEventSubscriber,
)
from app.main.blueprints.one_dev.services.kafka.error_analytics_events.error_analytics_event_subscriber import (
    ErrorAnalyticsEventSubscriber,
)


async def initialize_kafka_subscriber(_app: Sanic, loop: Any) -> None:
    """
    Initialize Kafka subscribers for session and error events,
    depending on their individual ENABLED flags.
    """
    kafka_config = _app.config.get("KAFKA", {})

    # Session event subscriber
    if kafka_config.get("SESSION_QUEUE", {}).get("ENABLED", False):
        session_event_subscriber = AnalyticsEventSubscriber(_app.config)
        _app.add_task(session_event_subscriber.consume())

    # Error event subscriber
    if kafka_config.get("ERROR_QUEUE", {}).get("ENABLED", False):
        error_event_subscriber = ErrorAnalyticsEventSubscriber(_app.config)
        _app.add_task(error_event_subscriber.consume())


async def close_weaviate_server(_app: Sanic, loop: Any) -> None:
    if hasattr(_app.ctx, "weaviate_client"):
        await _app.ctx.weaviate_client.async_client.close()
        _app.ctx.weaviate_client.sync_client.close()


async def setup_caches(app: Sanic) -> None:
    cache_config = app.config["REDIS_CACHE_HOSTS"]
    cache_registry.from_config(cache_config)


async def setup_tortoise(app: Sanic) -> None:
    await TortoiseWrapper.setup(config=app.config, orm_config=app.config["DB_CONNECTIONS"])


async def teardown_tortoise(app: Sanic) -> None:
    await TortoiseWrapper.teardown()


# Initializing listeners with background task only if it the background worker flag is enabled.
listeners = [
    (close_weaviate_server, ListenerEventTypes.BEFORE_SERVER_STOP.value),
    (setup_caches, ListenerEventTypes.BEFORE_SERVER_START.value),
    (initialize_kafka_subscriber, ListenerEventTypes.AFTER_SERVER_START.value),
    (setup_tortoise, ListenerEventTypes.BEFORE_SERVER_START.value),
    (teardown_tortoise, ListenerEventTypes.AFTER_SERVER_STOP.value),
]
