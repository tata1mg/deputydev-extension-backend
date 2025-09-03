from typing import Type, Union

from app.backend_common.utils.sanic_wrapper import CONFIG
from app.backend_common.utils.types.types import CloudProviders
from app.main.blueprints.deputy_dev.services.message_queue.parsers.message_parser.azure_bus_service_message_parser import (
    AzureBusServiceMessageParser,
)
from app.main.blueprints.deputy_dev.services.message_queue.parsers.message_parser.sqs_message_parser import (
    SQSMessageParser,
)

config = CONFIG.config


class MessageParserFactory:
    cloud_provider = config.get("CLOUD_PROVIDER")
    message_parsers = {
        CloudProviders.AZURE.value: AzureBusServiceMessageParser,
        CloudProviders.AWS.value: SQSMessageParser,
    }

    @classmethod
    def message_parser(cls) -> Type[Union[AzureBusServiceMessageParser, SQSMessageParser]]:
        return cls.message_parsers[cls.cloud_provider]
