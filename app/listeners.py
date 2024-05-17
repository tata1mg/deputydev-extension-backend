from torpedo.constants import ListenerEventTypes
from app.sqs.genai_subscriber import GenaiSubscriber

async def initialize_sqs_subscribes(_app, loop):
    """

    :param _app:
    :param loop:
    :return:
    """
    if (
        _app.config.get("SQS", {})
        .get("SUBSCRIBE", {})
        .get("GENAI", {})
        .get("ENABLED", False)
    ):
        genai_subscribe = GenaiSubscriber(_app.config)
        _app.add_task(genai_subscribe.subscribe())

listeners = [(initialize_sqs_subscribes, ListenerEventTypes.AFTER_SERVER_START.value)]
