class Response:
    def __init__(self, messages, message_model):
        if not messages:
            self.messages = []
        else:
            self.messages = [message_model(message) for message in messages]


class Attribute:
    def __init__(self, attribute_name: str, attribute_value: str):
        self.name = attribute_name
        self.value = attribute_value
