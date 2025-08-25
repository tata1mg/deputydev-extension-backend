from typing import Any, Dict, List, Optional

import ujson as json
from sanic.log import logger

from app.backend_common.services.message_queue.managers.message_queue_manager import (
    MessageQueueManager,
)
from app.backend_common.services.message_queue.message_queue_manager_factory import (
    MessageQueueManagerFactory,
)
from app.backend_common.utils.app_utils import log_combined_exception
from app.main.blueprints.deputy_dev.constants.constants import MESSAGE_QUEUE_LOG_LENGTH

"""
    implement get_queue_name function which will be returning queue name for every child class
"""


class BaseSubscriber:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config or {}
        self.message_queue_manager: MessageQueueManager = MessageQueueManagerFactory.manager()(config)
        self.queue_name = self.get_queue_name()
        logger.info(f"Queue name: {self.queue_name}")
        self.is_client_created = False

    def get_queue_name(self) -> str:
        raise NotImplementedError()

    async def init(self) -> None:
        if not self.is_client_created:
            await self.message_queue_manager.get_client(queue_name=self.queue_name)
            self.is_client_created = True

    async def publish(
        self, payload: Dict[str, Any], attributes: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        await self.init()
        payload = json.dumps(payload)
        try:
            await self.message_queue_manager.publish(payload=payload, attributes=attributes, batch=False, **kwargs)
        finally:
            self.is_client_created = False
            await self.message_queue_manager.close()

    async def bulk_publish(self, data: List[Dict[str, Any]], **kwargs: Any) -> None:
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

    def log_error(self, message: str, exception: Exception, payload: Optional[Dict[str, Any]] = None) -> None:
        message = message.format(queue_name=self.queue_name)
        if payload:
            message += " Payload =  " + json.dumps(payload)[:MESSAGE_QUEUE_LOG_LENGTH]
        log_combined_exception(message, exception)

    def log_info(self, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        message = message.format(queue_name=self.queue_name)
        if payload:
            message += " Payload = " + json.dumps(payload)[:MESSAGE_QUEUE_LOG_LENGTH]
        logger.info(message)

    def log_warn(self, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        message = message.format(queue_name=self.queue_name)
        if payload:
            message += " Payload =  " + json.dumps(payload)[:MESSAGE_QUEUE_LOG_LENGTH]
        logger.warn(message)
