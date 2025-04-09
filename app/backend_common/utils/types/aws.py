from enum import Enum


class AWSErrorMessages(Enum):
    AwsConnectionError = "Could not create connection with AWS: {error}"
    AwsSQSConnectionError = "Problem connecting to SQS queue, error: {error}"
    AwsSQSPayloadSize = "Payload size exceeds SQS limit of 256 KBs."
    AwsSQSPublishError = "Error publishing to sqs: {error}, retrying count: {count}"
    PARAMETER_REQUIRED = "Required parameters {param_key} for {queue_name}"
    PARAMETERS_NOT_ALLOWED = "Parameters {param_key} not allowed for {queue_name}"


class SQSQueueType(Enum):
    STANDARD_QUEUE = "sqs"
    STANDARD_QUEUE_FIFO = "sqs.fifo"


class AwsErrorType(Enum):
    SQSNotExist = "AWS.SimpleQueueService.NonExistentQueue"
    SQSRequestSizeExceeded = "AWS.SimpleQueueService.BatchRequestTooLong"
