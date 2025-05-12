from torpedo.constants import ListenerEventTypes

from app.main.blueprints.deputy_dev.services.message_queue.factories.message_queue_factory import (
    MessageQueueFactory,
)
from app.main.blueprints.deputy_dev.services.message_queue.message_queue_helper import (
    MessageQueueHelper,
)
from app.main.blueprints.one_dev.services.kafka.pixel_event_subscriber import (
    PixelEventSubscriber,
)


async def initialize_message_queue_subscribers(_app, loop):
    """

    :param _app:
    :param loop:
    :return:
    """
    if MessageQueueHelper.is_queue_enabled(_app.config, "GENAI"):
        genai_subscribe = MessageQueueFactory.genai_subscriber()(_app.config)
        _app.add_task(await genai_subscribe.subscribe())
    if MessageQueueHelper.is_queue_enabled(_app.config, "METASYNC"):
        meta_subscribe = MessageQueueFactory.meta_subscriber()(_app.config)
        _app.add_task(await meta_subscribe.subscribe())


async def initialize_kafka_subscriber(_app, loop):
    """
    Initialize Kafka subscriber for session events
    :param _app:
    :param loop:
    :return:
    """
    if _app.config.get("KAFKA", {}).get("ENABLED", False):
        session_event_subscriber = PixelEventSubscriber(_app.config)
        _app.add_task(session_event_subscriber.consume())

async def close_weaviate_server(_app, loop):
    if hasattr(_app.ctx, "weaviate_client"):
        await _app.ctx.weaviate_client.async_client.close()
        _app.ctx.weaviate_client.sync_client.close()


# Initializing listeners with background task only if it the background worker flag is enabled.
listeners = [
    (close_weaviate_server, ListenerEventTypes.BEFORE_SERVER_STOP.value),
    (initialize_kafka_subscriber, ListenerEventTypes.AFTER_SERVER_START.value),
    (initialize_message_queue_subscribers, ListenerEventTypes.AFTER_SERVER_START.value),
]
