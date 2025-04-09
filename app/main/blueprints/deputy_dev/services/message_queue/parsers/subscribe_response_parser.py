from typing import List, Type, Union
from app.main.blueprints.deputy_dev.models.dto.message_queue.common_message_queue_models import (
    Response,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.main.blueprints.deputy_dev.services.message_queue.parsers.message_parser.azure_bus_service_message_parser import (
        AzureBusServiceMessageParser,
    )
    from app.main.blueprints.deputy_dev.services.message_queue.parsers.message_parser.sqs_message_parser import (
        SQSMessageParser,
    )
    from app.main.blueprints.deputy_dev.models.dto.message_queue.sqs_message import (
        SQSMessage,
    )
    from app.main.blueprints.deputy_dev.models.dto.message_queue.azure_bus_service_message import (
        AzureBusServiceMessage,
    )


class SubscribeResponseParser:
    @classmethod
    def parse(
        cls,
        messages: List[Union["AzureBusServiceMessage", "SQSMessage"]],
        message_parser: Type[Union["SQSMessageParser", "AzureBusServiceMessageParser"]],
    ) -> Response:
        if not messages:
            messages = []
        else:
            messages = [message_parser.parse(message) for message in messages]
        return Response(messages=messages)
