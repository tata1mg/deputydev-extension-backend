import json

from app.main.blueprints.deputy_dev.models.dto.message_queue.base_message_queue_model import (
    Attribute,
)


class SQSMessage:
    def __init__(self, message: dict):
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
            self.body = None
            self.attributes = []
            self.receipt_handle = None
        else:
            self.body = self.decompress(message["Body"])
            message_attributes = message.get("MessageAttributes", {})
            self.attributes = [
                Attribute(attribute_name, message_attributes[attribute_name].get("StringValue"))
                for attribute_name in message_attributes
            ]
            self.receipt_handle = message["ReceiptHandle"]

    @staticmethod
    def decompress(message):
        return json.loads(message)
