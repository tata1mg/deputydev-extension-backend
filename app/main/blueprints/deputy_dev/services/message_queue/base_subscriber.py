import ujson as json
from app.backend_common.wrappers.message_queue.message_queue_factory import MessageQueueFactory
from app.backend_common.wrappers.message_queue.managers.message_queue_manager import MessageQueueManager
from sanic.log import logger
from app.backend_common.constants.error_messages import ErrorMessages
from app.backend_common.constants.success_messages import SuccessMessages
from app.backend_common.exception import RetryException
from app.backend_common.exception.exception import RateLimitError
from app.backend_common.utils.app_utils import log_combined_exception
from app.main.blueprints.deputy_dev.constants.sqs import SQS


"""
    implement get_queue_name function which will be returning queue name for every child class
"""


class BaseSubscriber:
    def __init__(self, config: dict):
        self.config = config or {}
        self.message_queue_manager: MessageQueueManager = MessageQueueFactory.manager()
        self.queue_name = self.get_queue_name()
        self.is_client_created = False

    def get_queue_name(self):
        raise NotImplementedError()

    async def init(self):
        if not self.is_client_created:
            await self.message_queue_manager.get_client(queue_name=self.queue_name)
            self.is_client_created = True

    async def publish(self, payload: dict, attributes=None, **kwargs):
        await self.init()
        payload = json.dumps(payload)
        try:
            await self.message_queue_manager.publish(payload=payload, attributes=attributes, batch=False, **kwargs)
        finally:
            self.is_client_created = False
            await self.message_queue_manager.close()

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

        return await self.message_queue_manager.publish(messages=data, batch=True, **kwargs)

    def log_error(self, message, exception, payload=None):
        message = message.format(queue_name=self.queue_name)
        if payload:
            message += " Payload =  " + json.dumps(payload)[: SQS.LOG_LENGTH.value]
        log_combined_exception(message, exception)

    def log_info(self, message, payload=None):
        message = message.format(queue_name=self.queue_name)
        if payload:
            message += " Payload = " + json.dumps(payload)[: SQS.LOG_LENGTH.value]
        logger.info(message)

    def log_warn(self, message, payload=None):
        message = message.format(queue_name=self.queue_name)
        if payload:
            message += " Payload =  " + json.dumps(payload)[: SQS.LOG_LENGTH.value]
        logger.warn(message)
