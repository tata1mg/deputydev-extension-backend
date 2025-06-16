from enum import Enum


class ErrorMessages(Enum):
    FIELD_REQUIRED = "{key} is required"
    TYPE_CHECK = "required {required_type}, received {received_type} for {key}"
    IN_CHECK = "{key} should be equal to any of these {acceptable_values}, not {param_value}"
    RETRIEVAL_FAIL_MSG = (
        "I don't understand what you are saying. "
        "I am a medical diagnostic agent and my knowledge is limited to this domain only."
    )
    QUEUE_EVENT_HANDLE_ERROR = "Message Queue {queue_name} | Unable to handle event"
    QUEUE_SUBSCRIBE_ERROR = "Message Queue {queue_name} | Unable to subscribe queue"
    TOKEN_COUNT_EXCEED_WARNING = "Token count exceeded for batch: {count}. Truncating down to {token_limit} tokens."
    QUEUE_MESSAGE_RETRY_EVENT = "Message Queue {queue_name} | Retried with error "
    QUEUE_TIMEOUT_ERROR = "Message Queue {queue_name} | Read Timeout Error"
    VCS_RATE_LIMIT_EVENT = "Message Queue {queue_name} | VCS rate limit breached with error "
