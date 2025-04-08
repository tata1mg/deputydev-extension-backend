import asyncio

import botocore.exceptions
from sanic.log import logger

from app.backend_common.constants.error_messages import ErrorMessages
from app.backend_common.constants.success_messages import SuccessMessages
from app.backend_common.exception import RetryException
from app.backend_common.exception.exception import RateLimitError
from app.main.blueprints.deputy_dev.services.message_queue.base_subscriber import (
    BaseSubscriber,
)
from app.main.blueprints.deputy_dev.services.message_queue.models.base_message_queue_model import (
    Response,
)



class SQSSubscriber(BaseSubscriber):
    @classmethod
    def format_attributes(cls):
        pass

    async def subscribe(self, **kwargs):
        max_no_of_messages = kwargs.get("max_no_of_messages", self.get_queue_config().get("MAX_MESSAGES", 1))
        wait_time_in_seconds = kwargs.get(
            "wait_time_in_seconds", self.get_queue_config().get("WAIT_TIME_IN_SECONDS", 5)
        )
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
                        # Process messages in parallel
                        tasks = [asyncio.create_task(self.handle_subscribe_event(message)) for message in messages]
                        await asyncio.gather(*tasks, return_exceptions=True)

                if show_configured_log:
                    self.log_info(SuccessMessages.QUEUE_SUCCESSFULLY_CONFIGURED.value)
                show_configured_log = False
            except botocore.exceptions.ReadTimeoutError:
                # We are simply passing this exception, since using return would break it out
                # of the loop
                logger.info("Message Queue subscribe event failed with read timeout error")
                continue
            except Exception as e:
                self.log_error(ErrorMessages.QUEUE_SUBSCRIBE_ERROR.value, e)

    async def receive_message(self, **kwargs):
        await self.init()
        response = await self.message_queue_manager.subscribe(**kwargs)
        message_model = self.message_queue_factory.message_model()
        response_model = Response(response.get("Messages"), message_model)
        logger.info(f"subscribe response model SQS: {response_model.messages}")
        return response_model

    async def purge(self, message):
        response = await self.message_queue_manager.purge(message)
        return response

    async def handle_subscribe_event(self, message):
        is_event_success = False
        body = message.body
        try:
            await self.event_handler.handle_event(body)
            is_event_success = True
            self.log_info(SuccessMessages.QUEUE_SUCCESSFULLY_HANDELED_EVENT.value, body)
        except RateLimitError as e:
            self.log_info(ErrorMessages.VCS_RATE_LIMIT_EVENT.value + e.message, body)
        except RetryException as e:
            self.log_info(ErrorMessages.QUEUE_MESSAGE_RETRY_EVENT.value + e.message, body)
        except Exception as e:
            self.log_error(ErrorMessages.QUEUE_EVENT_HANDLE_ERROR.value, e, body)

        if is_event_success:
            await self.purge(message=message)
