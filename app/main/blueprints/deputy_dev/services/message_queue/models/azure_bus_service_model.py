from app.main.blueprints.deputy_dev.services.message_queue.base_message_queue_model import Attribute
from azure.servicebus import ServiceBusReceivedMessage
import json


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
            self.lock_token = None
        else:
            self.body = message.body
            message_attributes = message.application_properties or {}
            self.attributes = [
                Attribute(attribute_name, attribute_value)
                for attribute_name, attribute_value in message_attributes.items()
            ]
            self.lock_token = message.lock_token  # require for deleting message

    @staticmethod
    def decompress(message):
        data = b"".join(message.body).decode("utf-8")
        return json.loads(data)
