from enum import Enum

from torpedo import CONFIG

sqs_config = CONFIG.config.get("SQS").get("SUBSCRIBE").get("GENAI")


class SQS(Enum):
    SUBSCRIBE = {
        "MAX_MESSAGES": sqs_config.get("MAX_MESSAGES", 1),
        "WAIT_TIME_IN_SECONDS": sqs_config.get("WAIT_TIME_IN_SECONDS", 5),
    }
    LOG_LENGTH = 500
