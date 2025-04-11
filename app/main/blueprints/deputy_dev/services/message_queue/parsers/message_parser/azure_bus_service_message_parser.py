import json

from azure.servicebus import ServiceBusReceivedMessage

from app.main.blueprints.deputy_dev.models.dto.message_queue.attribute import Attribute
from app.main.blueprints.deputy_dev.models.dto.message_queue.azure_bus_service_message import (
    AzureBusServiceMessage,
)


class AzureBusServiceMessageParser:
    @classmethod
    def parse(cls, message: ServiceBusReceivedMessage) -> AzureBusServiceMessage:
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
            body = None
            attributes = []
            received_message = None
        else:
            received_message = message  # require for deleting message
            body = cls.decompress(message.body)
            message_attributes = message.application_properties or {}
            attributes = [
                Attribute(name=attribute_name, value=str(attribute_value))
                for attribute_name, attribute_value in message_attributes.items()
            ]
        return AzureBusServiceMessage(body=body, attributes=attributes, received_message=received_message)

    @staticmethod
    def decompress(message):
        data = b"".join(message).decode("utf-8")
        return json.loads(data)
