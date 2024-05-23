from torpedo import CONFIG
from torpedo.constants import ListenerEventTypes

from app.sqs.genai_subscriber import GenaiSubscriber

config = CONFIG.config


async def initialize_sqs_subscribes(_app, loop):
    """

    :param _app:
    :param loop:
    :return:
    """
    if _app.config.get("SQS", {}).get("SUBSCRIBE", {}).get("GENAI", {}).get("ENABLED", False):
        genai_subscribe = GenaiSubscriber(_app.config)
        _app.add_task(await genai_subscribe.subscribe())


background_tasks = [
    (initialize_sqs_subscribes, ListenerEventTypes.AFTER_SERVER_START.value),
]


# Initializing listeners with background task only if it the background worker flag is enabled.
listeners = background_tasks if config.get("IS_BACKGROUND_WORKER_ENABLED") else []
