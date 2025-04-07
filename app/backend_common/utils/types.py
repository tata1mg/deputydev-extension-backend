from enum import Enum


class AWSErrorMessages(Enum):
    AwsConnectionError = "Could not create connection with AWS: {error}"
    AwsSQSConnectionError = "Problem connecting to SQS queue, error: {error}"
    AwsSQSPayloadSize = "Payload size exceeds SQS limit of 256 KBs."
    AwsSQSPublishError = "Error publishing to sqs: {error}, retrying count: {count}"
    PARAMETER_REQUIRED = "Required parameters {param_key} for {queue_name}"
    PARAMETERS_NOT_ALLOWED = "Parameters {param_key} not allowed for {queue_name}"


class AzureErrorMessages(Enum):
    PARAMETER_REQUIRED = "{param_key} is required for {queue_name}"
    PARAMETERS_NOT_ALLOWED = "{param_key} are not allowed for {queue_name}"
    AzureServiceBusConnectionError = "Azure Service Bus Connection Error: {error}"
    AzureServiceBusPublishError = "Azure Service Bus Publish Error: {error}, Retry Count: {count}"
    AzureServiceBusPayloadSize = "Message size exceeds the limit"


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
