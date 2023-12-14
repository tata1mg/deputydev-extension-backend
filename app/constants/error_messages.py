from enum import Enum


class ErrorMessages(Enum):
    FIELD_REQUIRED = '{key} is required'
    TYPE_CHECK = 'required {required_type}, received {received_type} for {key}'
    IN_CHECK = '{key} should be equal to any of these {acceptable_values}, not {param_value}'
    QUEUE_SUBSCRIBE_ERROR = 'SQS {queue_name} | Error in subscribing'
    QUEUE_EVENT_HANDLE_ERROR = 'SQS {queue_name} | Error in handling data'
