import json

from app.main.blueprints.deputy_dev.models.dto.message_queue.common_message_queue_models import (
    Attribute,
)
from app.main.blueprints.deputy_dev.models.dto.message_queue.sqs_message import (
    SQSMessage,
)


class SQSMessageParser:
    @classmethod
    def parse(cls, message: dict) -> SQSMessage:
        """
        Sample Message:
        {
          'MessageId': 'f5d37b3d-2cfb-4569-81c2-09acb84d56fb',
          'ReceiptHandle': 'AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy...',
          'MD5OfBody': '098f6bcd4621d373cade4e832627b4f6',
          'Body': 'Hello from SQS!',
          'Attributes': {
            'ApproximateReceiveCount': '1',
            'SentTimestamp': '1573251510774',
            'SenderId': 'AIDA...',
            'ApproximateFirstReceiveTimestamp': '1573251510777'
          },
          'MessageAttributes': {
            'Attribute1': {
              'StringValue': 'Value1',
              'DataType': 'String'
            },
            'Attribute2': {
              'StringValue': 'Value2',
              'DataType': 'String'
            }
          }
        }
        """
        if not message:
            body = None
            attributes = []
            receipt_handle = None
        else:
            body = cls.decompress(message["Body"])
            message_attributes = message.get("MessageAttributes", {})
            attributes = [
                Attribute(name=attribute_name, value=message_attributes[attribute_name].get("StringValue"))
                for attribute_name in message_attributes
            ]
            receipt_handle = message["ReceiptHandle"]
        return SQSMessage(body=body, attributes=attributes, receipt_handle=receipt_handle)

    @staticmethod
    def decompress(message):
        return json.loads(message)
