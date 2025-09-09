import asyncio
from typing import Any

from azure.core.exceptions import (
    ServiceRequestError,
    ServiceRequestTimeoutError,
    ServiceResponseTimeoutError,
)
from azure.servicebus.aio import AutoLockRenewer, ServiceBusReceiver
from sanic.log import logger

from app.backend_common.constants.error_messages import ErrorMessages
from app.backend_common.constants.success_messages import SuccessMessages
from app.backend_common.exception.exception import RateLimitError
from app.main.blueprints.deputy_dev.services.message_queue.factories.message_parser_factory import (
    MessageParserFactory,
)
from app.main.blueprints.deputy_dev.services.message_queue.parsers.subscribe_response_parser import (
    SubscribeResponseParser,
)
from app.main.blueprints.deputy_dev.services.message_queue.subscribers.base.base_subscriber import (
    BaseSubscriber,
)
from deputydev_core.exceptions.exceptions import RetryException


class AzureBusServiceSubscriber(BaseSubscriber):
    async def subscribe(self, **kwargs: Any) -> None:
        max_no_of_messages = kwargs.get("max_no_of_messages", self.get_queue_config().get("MAX_MESSAGES", 1))
        wait_time_in_seconds = kwargs.get(
            "wait_time_in_seconds", self.get_queue_config().get("WAIT_TIME_IN_SECONDS", 5)
        )
        show_configured_log = True
        while True:
            try:
                receiver: ServiceBusReceiver = None
                lock_renewer: AutoLockRenewer = None
                response, receiver, lock_renewer = await self.receive_message(
                    max_no_of_messages=max_no_of_messages,
                    wait_time_in_seconds=wait_time_in_seconds,
                )
                if response:
                    messages = response.messages
                    if messages:
                        # Process messages in parallel
                        tasks = [
                            asyncio.create_task(self.handle_subscribe_event(message, receiver)) for message in messages
                        ]
                        await asyncio.gather(*tasks, return_exceptions=True)
                if show_configured_log:
                    self.log_info(SuccessMessages.QUEUE_SUCCESSFULLY_CONFIGURED.value)
                show_configured_log = False
            except (ServiceRequestTimeoutError, ServiceResponseTimeoutError) as error:
                self.log_error(ErrorMessages.QUEUE_TIMEOUT_ERROR.value, error)
                logger.info("Message Queue subscribe event failed with read timeout error")
            except ServiceRequestError:
                logger.info("Message Queue subscribe event failed with read timeout error")
            except Exception as e:  # noqa: BLE001
                self.log_error(ErrorMessages.QUEUE_SUBSCRIBE_ERROR.value, e)
            finally:
                if receiver:
                    await receiver.close()
                if lock_renewer:
                    await lock_renewer.close()
                await self.message_queue_manager.close()

    async def receive_message(self, **kwargs: Any) -> None:
        await self.init()
        messages, receiver, lock_renewer = await self.message_queue_manager.subscribe(**kwargs)
        message_parser = MessageParserFactory.message_parser()
        response_model = SubscribeResponseParser.parse(messages, message_parser)
        logger.info(f"subscribe response model Azure Bus Service: {response_model.messages}")
        return response_model, receiver, lock_renewer

    async def purge(self, message: Any, receiver: ServiceBusReceiver) -> None:
        response = await self.message_queue_manager.purge(message, receiver)
        return response

    async def handle_subscribe_event(self, message: Any, receiver: ServiceBusReceiver) -> None:
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
        except Exception as e:  # noqa: BLE001
            self.log_error(ErrorMessages.QUEUE_EVENT_HANDLE_ERROR.value, e, body)

        if is_event_success:
            await self.purge(message=message, receiver=receiver)
