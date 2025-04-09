from enum import Enum


class AzureErrorMessages(Enum):
    PARAMETER_REQUIRED = "Required parameters {param_key} for {queue_name}"
    PARAMETERS_NOT_ALLOWED = "Parameters {param_key} not allowed for {queue_name}"
    AzureServiceBusConnectionError = "Problem connecting to Azure Service Bus, error: {error}"
    AzureServiceBusPublishError = "Error publishing to Azure Bus Service: {error}, retrying count: {count}"
    AzureServiceBusPayloadSize = "Payload size exceeds Azure Bus Service limit of 256 KBs."


class AzureBusServiceQueueType(Enum):
    SESSION_ENABLED = "session_enabled"
    SESSION_DISABLED = "session_disabled"
