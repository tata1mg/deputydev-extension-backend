from enum import Enum


class AWSErrorMessages(Enum):
    AwsConnectionError = "Could not create connection with AWS: {error}"
    AwsSQSConnectionError = "Problem connecting to SQS queue, error: {error}"
    AwsSQSPayloadSize = "Payload size exceeds SQS limit of 256 KBs."
    AwsSQSPublishError = "Error publishing to sqs: {error}, retrying count: {count}"
    PARAMETER_REQUIRED = "Required parameters {param_key} for {queue_name}"
    PARAMETERS_NOT_ALLOWED = "Parameters {param_key} not allowed for {queue_name}"


class AzureErrorMessages(Enum):
    PARAMETER_REQUIRED = "Required parameters {param_key} for {queue_name}"
    PARAMETERS_NOT_ALLOWED = "Parameters {param_key} not allowed for {queue_name}"
    AzureServiceBusConnectionError = "Problem connecting to Azure Service Bus, error: {error}"
    AzureServiceBusPublishError = "Error publishing to Azure Bus Service: {error}, retrying count: {count}"
    AzureServiceBusPayloadSize = "Payload size exceeds Azure Bus Service limit of 256 KBs."


class SQSQueueType(Enum):
    STANDARD_QUEUE = "sqs"
    STANDARD_QUEUE_FIFO = "sqs.fifo"


class AzureBusServiceQueueType(Enum):
    SESSION_ENABLED = "session_enabled"
    SESSION_DISABLED = "session_disabled"


class AwsErrorType(Enum):
    SQSNotExist = "AWS.SimpleQueueService.NonExistentQueue"
    SQSRequestSizeExceeded = "AWS.SimpleQueueService.BatchRequestTooLong"


class DelayQueueTime(Enum):
    MINIMUM_TIME = 0
    MAXIMUM_TIME = 300


class CloudProviders(Enum):
    AZURE = "AZURE"
    AWS = "AWS"
