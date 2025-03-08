from enum import Enum


class SuccessMessages(Enum):
    QUEUE_SUCCESSFULLY_CONFIGURED = "SQS {queue_name} | Configured"
    QUEUE_SUCCESSFULLY_HANDELED_EVENT = "SQS {queue_name} | Successfully handled event"
