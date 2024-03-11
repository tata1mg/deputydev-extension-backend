import asyncio

import ujson as json
from commonutils import BaseSQSWrapper
from sanic.log import logger

from app.utils import log_combined_exception

from ..constants import SQS as Constant
from ..constants import ErrorMessages, SuccessMessages
from .model import Response

"""
    implement get_queue_name function which will be returning queue name for every child class
"""


class Base:
    def __init__(self, config: dict, event_handler):
        self.config = config or {}
        self.sqs_manager = BaseSQSWrapper(config)
        self._create_client_lock = asyncio.Semaphore(1)
        self.is_client_created = False
        self.event_handler = event_handler

    async def init(self):
        if not self.is_client_created:
            await self.sqs_manager.get_sqs_client(queue_name=self.get_queue_name())
            self.is_client_created = True

    async def publish(self, payload: dict, attributes=None, **kwargs):
        await self.init()
        payload = json.dumps(payload)
        response = await self.sqs_manager.publish_to_sqs(payload=payload, attributes=attributes, batch=False, **kwargs)
        return response

    async def bulk_publish(self, data: list, **kwargs):
        # '''
        # format of data is same as the all params that we send in single publish call
        # :param data: contains list of dict(payload, attributes, message_group_id, message_deduplication_id etc..)
        # :param kwargs: contains max_retries etc.
        # :return:
        # '''
        await self.init()
        if len(data) > 10:
            raise Exception("at max 10 messages can be send in a batch")
        for datum in data:
            datum["payload"] = json.dumps(datum["payload"])

        return await self.sqs_manager.publish_to_sqs(messages=data, batch=True, **kwargs)

    async def subscribe(self, **kwargs):
        max_no_of_messages = kwargs.get("max_no_of_messages", Constant.SUBSCRIBE.value["MAX_MESSAGES"])
        wait_time_in_seconds = kwargs.get("wait_time_in_seconds", Constant.SUBSCRIBE.value["WAIT_TIME_IN_SECONDS"])
        show_configured_log = True
        while True:
            try:
                response = await self.receive_message(
                    max_no_of_messages=max_no_of_messages,
                    wait_time_in_seconds=wait_time_in_seconds,
                )
                if response:
                    messages = response.messages
                    if messages:
                        for message in messages:
                            await self.handle_subscribe_event(message)
                if show_configured_log:
                    self.log_info(SuccessMessages.QUEUE_SUCCESSFULLY_CONFIGURED.value)
                show_configured_log = False
            except Exception as e:
                self.log_error(ErrorMessages.QUEUE_SUBSCRIBE_ERROR.value, e)

    async def receive_message(self, **kwargs):
        await self.init()
        response = await self.sqs_manager.subscribe(**kwargs)
        response_model = Response(response)
        response_model.messages = [self.decompress(message) for message in response_model.messages]
        return response_model

    async def handle_subscribe_event(self, message):
        is_event_success = False
        body = message.body
        try:
            await self.event_handler.handle_event(body)
            is_event_success = True
            self.log_info(SuccessMessages.QUEUE_SUCCESSFULLY_HANDELED_EVENT.value, body)
        except Exception as e:
            self.log_error(ErrorMessages.QUEUE_EVENT_HANDLE_ERROR.value, e, body)

        if is_event_success:
            await self.purge(receipt_handle=message.receipt_handle)

    async def purge(self, receipt_handle):
        response = await self.sqs_manager.purge(receipt_handle)
        return response

    def enable_worker(self):
        if "ENABLE" in self.worker_config():
            return self.worker_config()["ENABLE"]
        return self.config.get("ENABLE_WORKER")

    @staticmethod
    def decompress(message):
        message.body = json.loads(message.body)
        return message

    def log_error(self, message, exception, payload=None):
        message = message.format(queue_name=self.get_queue_name())
        if payload:
            message += " Payload =  " + json.dumps(payload)[: Constant.LOG_LENGTH.value]
        log_combined_exception(message, exception)

    def log_info(self, message, payload=None):
        message = message.format(queue_name=self.get_queue_name())
        if payload:
            message += " Payload = " + json.dumps(payload)[: Constant.LOG_LENGTH.value]
        logger.info(message)
