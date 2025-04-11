import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from azure.mgmt.servicebus import ServiceBusManagementClient
from azure.servicebus import (
    NEXT_AVAILABLE_SESSION,
    ServiceBusMessage,
    ServiceBusMessageBatch,
    ServiceBusReceivedMessage,
)
from azure.servicebus.aio import AutoLockRenewer
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient
from azure.servicebus.aio import ServiceBusReceiver
from azure.servicebus.exceptions import MessageSizeExceededError, ServiceBusError
from sanic.log import logger

from app.backend_common.services.message_queue.managers.message_queue_manager import (
    MessageQueueManager,
)
from app.backend_common.utils.types.azure import (
    AzureBusServiceQueueType,
    AzureErrorMessages,
)
from app.backend_common.utils.types.types import DelayQueueTime
from app.main.blueprints.deputy_dev.models.dto.message_queue.azure_bus_service_message import (
    AzureBusServiceMessage,
)


class AzureServiceBusManager(MessageQueueManager):
    def __init__(self, config: dict, config_key: str = "AZURE_BUS_SERVICE"):
        self.config = config.get(config_key, {})
        self._app_config = config
        self.client: Optional[AsyncServiceBusClient] = None
        self.async_credential = AsyncDefaultAzureCredential()
        self.sync_credential = DefaultAzureCredential()
        self.queue_name = None
        self.queue_type = None

    async def get_client(self, queue_name):
        fully_qualified_namespace = self.config.get("NAMESPACE_FQDN")
        logging_enabled = self.config.get("LOGGING_ENABLED") or False
        retry_total = self.config.get("RETRY_TOTAL", 3)
        retry_backoff_factor: float = self.config.get("RETRY_BACKOFF_FACTOR", 0.8)
        retry_backoff_max: float = self.config.get("RETRY_BACKOFF_MAX", 120)
        retry_mode: str = self.config.get("RETRY_MODE", "exponential")

        self.client: AsyncServiceBusClient = AsyncServiceBusClient(
            fully_qualified_namespace=fully_qualified_namespace,
            credential=self.async_credential,
            retry_total=retry_total,
            retry_backoff_factor=retry_backoff_factor,
            retry_mode=retry_mode,
            retry_backoff_max=retry_backoff_max,
            logging_enable=logging_enabled,
        )
        self.queue_name = queue_name
        self.queue_type = self._get_queue_type()
        return self.client

    async def publish(self, payload: str = None, messages: list = None, attributes: dict = None, batch=False, **kwargs):
        """
        :param messages: list of messages to be sent to Azure Service Bus for batch requests
        :param payload: message payload to be sent to Azure Service Bus for single events
        :param attributes: message properties
        :param batch: tells multiple message or single message
        :return: True or False
        """
        messages, payload = messages or [], payload or {}
        session_id = kwargs.get("session_id")  # message_group_id
        message_id = kwargs.get("message_id")  # message_deduplication_id
        self._validate_publish_to_service_bus(session_id, message_id)

        _send, _retry_count, sent_response_data = False, 0, {}
        _max_retries = kwargs.get("max_retries") or 3

        while not _send and _retry_count < _max_retries:
            try:
                if batch:  # Batch messages
                    await self._send_message(
                        messages=messages,
                        session_id=session_id,
                        message_id=message_id,
                        attributes=attributes,
                        batch=batch,
                    )
                else:  # Single message
                    await self._send_message(
                        payload, session_id=session_id, message_id=message_id, attributes=attributes, batch=batch
                    )
                    _send = True
            except MessageSizeExceededError as err:
                raise Exception(AzureErrorMessages.AzureServiceBusPayloadSize.value.format())
            except ServiceBusError as err:
                logger.info(AzureErrorMessages.AzureServiceBusPublishError.value.format(error=err, count=_retry_count))
            except Exception as e:
                logger.info(AzureErrorMessages.AzureServiceBusPublishError.value.format(error=e, count=_retry_count))
            finally:
                _retry_count += 1

        return _send

    async def _send_message(
        self, payload: str = None, messages: List[str] = None, attributes: dict = None, batch=False, **kwargs
    ) -> None:
        sender = self.client.get_queue_sender(self.queue_name)
        if not batch:
            if self.queue_type == AzureBusServiceQueueType.SESSION_ENABLED:
                session_id = kwargs.get("session_id")
                message_id = kwargs.get("message_id")
                message = ServiceBusMessage(
                    payload, session_id=session_id, message_id=message_id, application_properties=attributes
                )
            else:
                delay_seconds = kwargs.get("delay_seconds", DelayQueueTime.MINIMUM_TIME.value)
                scheduled_enqueue_time_utc = None
                if (
                    delay_seconds
                    and isinstance(delay_seconds, int)
                    and DelayQueueTime.MINIMUM_TIME.value < delay_seconds < DelayQueueTime.MAXIMUM_TIME.value
                ):
                    scheduled_enqueue_time_utc = datetime.utcnow() + timedelta(seconds=delay_seconds)
                message = ServiceBusMessage(
                    payload, application_properties=attributes, scheduled_enqueue_time_utc=scheduled_enqueue_time_utc
                )

            async with sender:
                await sender.send_messages(message)
            await sender.close()
        else:
            if self.queue_type == AzureBusServiceQueueType.SESSION_DISABLED:
                async with sender:
                    message_batch: ServiceBusMessageBatch = await sender.create_message_batch()
                    for msg in messages:
                        service_bus_message = ServiceBusMessage(msg, application_properties=attributes or {})
                        try:
                            message_batch.add_message(service_bus_message)
                        except ValueError:
                            # Message too large for current batch, send current batch
                            await sender.send_messages(message_batch)
                            # Start new batch
                            message_batch = await sender.create_message_batch()
                            message_batch.add_message(service_bus_message)
                    # Send the final batch
                    await sender.send_messages(message_batch)
            # TODO: have few doubts in session_enabled bulk publish

    async def close(self):
        if self.client:
            await self.client.close()
        if self.async_credential:
            await self.async_credential.close()
        if self.sync_credential:
            self.sync_credential.close()

    async def subscribe(self, **kwargs) -> Tuple[List[ServiceBusReceivedMessage], ServiceBusReceiver, AutoLockRenewer]:
        if not self.client or not self.queue_name:
            raise ValueError("Service Bus client or entity name is not initialized")
        max_message_count = kwargs.get("max_no_of_messages")
        max_wait_time = kwargs.get("wait_time_in_seconds")
        lock_renewer = AutoLockRenewer()
        try:
            if self.queue_type == AzureBusServiceQueueType.SESSION_DISABLED:
                receiver = self.client.get_queue_receiver(self.queue_name)
                await receiver.__aenter__()
                received_msgs = await receiver.receive_messages(
                    max_message_count=max_message_count, max_wait_time=max_wait_time
                )
                for message in received_msgs:
                    lock_renewer.register(receiver, message, max_lock_renewal_duration=self.config["LOCK_ENABLE_TIME"])
            else:
                receiver = self.client.get_queue_receiver(self.queue_name, session_id=NEXT_AVAILABLE_SESSION)
                await receiver.__aenter__()
                received_msgs = await receiver.receive_messages(
                    max_message_count=max_message_count, max_wait_time=max_wait_time
                )
                lock_renewer.register(
                    receiver, receiver.session, max_lock_renewal_duration=self.config["LOCK_ENABLE_TIME"]
                )
            return received_msgs, receiver, lock_renewer
        except Exception as e:
            await receiver.close()
            await lock_renewer.close()
            raise e

    def _validate_publish_to_service_bus(self, session_id: str, message_id: str):
        queue_type = self._get_queue_type()
        if queue_type == AzureBusServiceQueueType.SESSION_ENABLED:
            if not session_id:
                raise Exception(
                    AzureErrorMessages.PARAMETER_REQUIRED.value.format(
                        param_key="session_id", queue_name="Azure Service Bus topic publish"
                    )
                )
        else:
            if session_id or message_id:
                raise Exception(
                    AzureErrorMessages.PARAMETERS_NOT_ALLOWED.value.format(
                        param_key="session_id or message_id", queue_name="Azure Service Bus queue publish"
                    )
                )

    def _get_queue_type(self):
        if self.queue_type:
            return self.queue_type
        client = ServiceBusManagementClient(self.sync_credential, self.config.get("SUBSCRIPTION_ID"))
        queue = client.queues.get(self.config.get("RESOURCE_GROUP"), self.config.get("NAMESPACE"), self.queue_name)
        self.queue_type = (
            AzureBusServiceQueueType.SESSION_ENABLED
            if queue.requires_session
            else AzureBusServiceQueueType.SESSION_DISABLED
        )
        return self.queue_type

    async def purge(self, message: AzureBusServiceMessage, receiver: ServiceBusReceiver):
        await receiver.complete_message(message.received_message)
