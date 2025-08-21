from typing import Any, Dict, List

import botocore.exceptions
from aiobotocore.client import AioBaseClient
from aiobotocore.session import ClientCreatorContext
from sanic.log import logger

from app.backend_common.service_clients.sqs.sqs_client import SQSClient
from app.backend_common.services.message_queue.managers.message_queue_manager import (
    MessageQueueManager,
)
from app.backend_common.utils.types.aws import (
    AWSErrorMessages,
    AwsErrorType,
    SQSQueueType,
)
from app.backend_common.utils.types.types import DelayQueueTime


class SQSManager(MessageQueueManager):
    def __init__(self, config: Dict[str, Any], config_key: str = "SQS") -> None:
        self.config = config.get(config_key, {})
        self._app_config = config
        self.client = None
        self.queue_url = None

    async def get_client(self, queue_name: str) -> ClientCreatorContext:
        aws_access_key_id = self.config.get("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = self.config.get("AWS_SECRET_ACCESS_KEY")
        region = self.config.get("SQS_REGION", "ap-south-1")
        endpoint_url = self.config.get("SQS_ENDPOINT_URL") or None
        max_connections = self.config.get("SQS_MAX_CONNECTIONS") or None
        connect_timeout = self.config.get("connect_timeout") or None
        read_timeout = self.config.get("read_timeout") or None
        signature_version = self.config.get("signature_version") or None
        concurrency_limit = self._app_config.get("CONCURRENCY_LIMIT") or 0
        concurrency_limit_host = self._app_config.get("CONCURRENCY_LIMIT_HOST") or 0
        client = await SQSClient.create_sqs_client(
            region,
            aws_secret_access_key=aws_secret_access_key,
            aws_access_key_id=aws_access_key_id,
            endpoint_url=endpoint_url,
            max_pool_connections=max_connections,
            concurrency_limit=concurrency_limit,
            concurrency_limit_host=concurrency_limit_host,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            signature_version=signature_version,
        )

        self.client: AioBaseClient = await client.__aenter__()
        if client and queue_name and len(queue_name) > 0:
            queue_url = await self._get_queue_url(queue_name)
            self.queue_url = queue_url
        return client

    async def publish(
        self,
        messages: List[Dict[str, Any]] | None = None,
        attributes: Dict[str, Any] | None = None,
        payload: str | None = None,
        batch: bool = True,
        **kwargs: Any,
    ) -> bool:
        """
        :param messages: entity payload to be sent to SQS queue for batch requests
        :param payload: entity payload to be sent to SQS queue for not batch requests (single events)
        :param attributes: message attributes related to payload
        :param batch: tells if request is a batch request or not.
        :return: True or False
        """
        messages, attributes, payload = messages or [], attributes or {}, payload or ""
        message_group_id, message_deduplication_id = (
            kwargs.get("message_group_id"),
            kwargs.get("message_deduplication_id"),
        )
        delay_seconds = kwargs.get("delay_seconds", DelayQueueTime.MINIMUM_TIME.value)
        queue_type = self._get_queue_type()
        self._validate_publish(queue_type, message_group_id, message_deduplication_id)
        _send, _retry_count, sent_response_data = False, 0, {}
        _max_retries = kwargs.get("max_retries") or 3
        while _send is not True and _retry_count < _max_retries:
            try:
                if not batch:
                    send_message_data = {
                        "QueueUrl": self.queue_url,
                        "MessageBody": payload,
                        "MessageAttributes": attributes,
                    }

                    if queue_type == SQSQueueType.STANDARD_QUEUE_FIFO.value:
                        send_message_data["MessageGroupId"] = message_group_id
                        if message_deduplication_id:
                            send_message_data["MessageDeduplicationId"] = message_deduplication_id
                    elif (
                        delay_seconds
                        and isinstance(delay_seconds, int)
                        and DelayQueueTime.MINIMUM_TIME.value < delay_seconds < DelayQueueTime.MAXIMUM_TIME.value
                    ):
                        send_message_data.update({"DelaySeconds": delay_seconds})

                    sent_response_data = await self.client.send_message(**send_message_data)
                else:
                    sent_response_data = await self.client.send_message_batch(QueueUrl=self.queue_url, Entries=messages)
                _send = True
            except botocore.exceptions.ClientError as err:
                if err.response["Error"]["Code"] == AwsErrorType.SQSRequestSizeExceeded.value:
                    raise Exception(AWSErrorMessages.AwsSQSPayloadSize.value)
                else:
                    logger.info(AWSErrorMessages.AwsSQSPublishError.value.format(error=err, count=_retry_count))
            except Exception as e:  # noqa: BLE001
                logger.info(AWSErrorMessages.AwsSQSPublishError.value.format(error=e, count=_retry_count))
            finally:
                _retry_count += 1
        if kwargs.get("return_response") and _send:
            return sent_response_data
        return _send

    async def _get_queue_url(self, queue_name: str) -> str:
        try:
            response = await self.client.get_queue_url(QueueName=queue_name)
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == AwsErrorType.SQSNotExist.value:
                raise Exception(
                    AWSErrorMessages.AwsSQSConnectionError.value.format(error=err.response["Error"]["Code"])
                )
            else:
                raise Exception(
                    AWSErrorMessages.AwsSQSConnectionError.value.format(error=err.response["Error"]["Code"])
                )
        queue_url = response.get("QueueUrl")
        return queue_url

    async def get_queue_arn(self, queue_name: str) -> str:
        queue_url = await self._get_queue_url(queue_name)
        response = await self._get_queue_attributes(queue_url=queue_url, attribute_names=["QueueArn"])
        return response.get("Attributes").get("QueueArn")

    async def subscribe(self, **kwargs: Any) -> Dict[str, Any]:
        max_no_of_messages = kwargs.get("max_no_of_messages") or 1
        wait_time_in_seconds = kwargs.get("wait_time_in_seconds") or 5
        message_attribute_names = kwargs.get("message_attribute_names") or ["All"]
        attribute_names = kwargs.get("attribute_names") or ["All"]

        if kwargs.get("visibility_timeout") is not None:
            visibility_timeout = kwargs.get("visibility_timeout")
            messages = await self.client.receive_message(
                QueueUrl=self.queue_url,
                WaitTimeSeconds=wait_time_in_seconds,
                MaxNumberOfMessages=max_no_of_messages,
                AttributeNames=attribute_names,
                MessageAttributeNames=message_attribute_names,
                VisibilityTimeout=visibility_timeout,
            )
        else:
            messages = await self.client.receive_message(
                QueueUrl=self.queue_url,
                WaitTimeSeconds=wait_time_in_seconds,
                MaxNumberOfMessages=max_no_of_messages,
                AttributeNames=attribute_names,
                MessageAttributeNames=message_attribute_names,
            )
        return messages

    async def close(self) -> None:
        await self.client.close()

    async def purge(self, message: Any) -> None:
        await self.client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=message.receipt_handle)

    @staticmethod
    def _validate_publish(queue_type: str, message_group_id: str, message_deduplication_id: str) -> None:
        if queue_type == SQSQueueType.STANDARD_QUEUE_FIFO.value:
            if not message_group_id:
                raise Exception(
                    AWSErrorMessages.PARAMETER_REQUIRED.value.format(
                        param_key="message_group_id", queue_name="sqs fifo queue push"
                    )
                )
        else:
            if message_group_id or message_deduplication_id:
                raise Exception(
                    AWSErrorMessages.PARAMETERS_NOT_ALLOWED.value.format(
                        param_key="message_group_id and message_deduplication_id", queue_name="sqs standard queue push"
                    )
                )

    def _get_queue_type(self) -> str:
        if ".fifo" in self.queue_url:
            return SQSQueueType.STANDARD_QUEUE_FIFO.value
        return SQSQueueType.STANDARD_QUEUE.value

    async def _get_queue_attributes(self, queue_url: str, attribute_names: List[str] = []) -> Dict[str, Any]:
        try:
            response = await self.client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=attribute_names)
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == AwsErrorType.SQSNotExist.value:
                raise Exception(
                    AWSErrorMessages.AwsSQSConnectionError.value.format(error=err.response["Error"]["Code"])
                )
            else:
                raise Exception(
                    AWSErrorMessages.AwsSQSConnectionError.value.format(error=err.response["Error"]["Code"])
                )
        return response
