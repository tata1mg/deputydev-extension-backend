from enum import Enum


class DelayQueueTime(Enum):
    MINIMUM_TIME = 0
    MAXIMUM_TIME = 300


class CloudProviders(Enum):
    AZURE = "AZURE"
    AWS = "AWS"
