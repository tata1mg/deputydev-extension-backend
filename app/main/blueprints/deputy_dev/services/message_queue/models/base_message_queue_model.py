from app.main.blueprints.deputy_dev.services.message_queue.message_queue_factory import MessageQueueFactory


class Response:
    def __init__(self, messages):
        if not messages:
            self.messages = []
        else:
            self.messages = [MessageQueueFactory.message_model()(message) for message in messages]


class Attribute:
    def __init__(self, attribute_name: str, attribute_value: str):
        self.name = attribute_name
        self.value = attribute_value
