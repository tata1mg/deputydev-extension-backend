from torpedo.constants import ListenerEventTypes

from app.main.blueprints.deputy_dev.services.sqs.genai_subscriber import GenaiSubscriber
from app.main.blueprints.deputy_dev.services.sqs.meta_subscriber import MetaSubscriber
from app.main.blueprints.one_dev.services.kafka.session_event_subscriber import SessionEventSubscriber


async def initialize_sqs_subscribes(_app, loop):
    """

    :param _app:
    :param loop:
    :return:
    """
    if _app.config.get("SQS", {}).get("SUBSCRIBE", {}).get("GENAI", {}).get("ENABLED", False):
        genai_subscribe = GenaiSubscriber(_app.config)
        _app.add_task(await genai_subscribe.subscribe())

    if _app.config.get("SQS", {}).get("SUBSCRIBE", {}).get("METASYNC", {}).get("ENABLED", False):
        meta_subscribe = MetaSubscriber(_app.config)
        _app.add_task(await meta_subscribe.subscribe())

async def initialize_kafka_subscriber(_app, loop):
    """
    Initialize Kafka subscriber for session events
    :param _app:
    :param loop:
    :return:
    """
    if _app.config.get("KAFKA", {}).get("ENABLED", False):
        session_event_subscriber = SessionEventSubscriber(_app.config)
        _app.add_task(session_event_subscriber.consume())


# Initializing listeners with background task only if it the background worker flag is enabled.
listeners = [
    (initialize_kafka_subscriber, ListenerEventTypes.AFTER_SERVER_START.value),
    (initialize_sqs_subscribes, ListenerEventTypes.AFTER_SERVER_START.value),
]
