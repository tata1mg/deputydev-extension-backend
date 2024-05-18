from enum import Enum


class SQS(Enum):
    SUBSCRIBE = {"MAX_MESSAGES": 2, "WAIT_TIME_IN_SECONDS": 5}
    LOG_LENGTH = 500
