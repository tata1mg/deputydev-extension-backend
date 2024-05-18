from enum import Enum


class ErrorMessages(Enum):
    FIELD_REQUIRED = "{key} is required"
    TYPE_CHECK = "required {required_type}, received {received_type} for {key}"
    IN_CHECK = "{key} should be equal to any of these {acceptable_values}, not {param_value}"
    RETRIEVAL_FAIL_MSG = (
        "I don't understand what you are saying. "
        "I am a medical diagnostic agent and my knowledge is limited to this domain only."
    )
    QUEUE_EVENT_HANDLE_ERROR = "SQS {queue_name} | Unable to handle event"
    QUEUE_SUBSCRIBE_ERROR = "SQS {queue_name} | Unable to subscribe queue"
    # RETRIEVAL_FAIL_MSG = "Oops! We couldn't process your Lab report. Please make sure it's a valid format and try again",
    # RETRIEVAL_FAIL_MSG =  "Oops! We couldn't process your image. Please make sure it's a valid format and try again"
