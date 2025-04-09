import json

from azure.servicebus import ServiceBusReceivedMessage

from app.main.blueprints.deputy_dev.models.dto.message_queue.base_message_queue_model import (
    Attribute,
)


class AzureBusServiceMessage:
    def __init__(self, message: ServiceBusReceivedMessage):
        """
        sample of  ServiceBusReceivedMessage:
        ServiceBusReceivedMessage(
            body='Hello from Azure Service Bus!',
            message_id='abc-123',
            application_properties={'key': 'value'},
            session_id=None,
            content_type='text/plain',
            delivery_count=1,
            lock_token='UUID',
            enqueued_time_utc=datetime,
            expires_at_utc=datetime,
            partition_key=None,
            subject=None,
        )
        """
        if not message:
            self.body = None
            self.attributes = []
            self.received_message = None
        else:
            self.received_message = message  # require for deleting message
            self.body = self.decompress(message.body)
            message_attributes = message.application_properties or {}
            self.attributes = [
                Attribute(attribute_name, attribute_value)
                for attribute_name, attribute_value in message_attributes.items()
            ]

    @staticmethod
    def decompress(message):
        data = b"".join(message).decode("utf-8")
        return json.loads(data)
