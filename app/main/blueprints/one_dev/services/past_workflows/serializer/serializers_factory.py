from app.main.blueprints.one_dev.constants.serializers_constants import SerializerTypes
from app.main.blueprints.one_dev.services.past_workflows.serializer.base_serializers import BaseSerializer
from typing import Any, Dict, List

from app.main.blueprints.one_dev.services.past_workflows.serializer.past_chats import PastChatsSerializer
from app.main.blueprints.one_dev.services.past_workflows.serializer.past_sessions import PastSessionsSerializer

class SerializersFactory:
    """
    A factory class for creating serializer instances based on the provided type.

    This class maps serializer types to their corresponding serializer classes.
    """

    FACTORIES = {
        SerializerTypes.PAST_SESSIONS: PastSessionsSerializer,
        SerializerTypes.PAST_CHATS: PastChatsSerializer
    }

    @classmethod
    def get_serializer_service(cls, raw_data: List[Dict[str, Any]], type: SerializerTypes) -> BaseSerializer:
        """
        Retrieves the appropriate serializer service based on the specified type.

        Args:
            raw_data (List[Dict[str, Any]]): The raw data to be serialized.
            type (SerializerTypes): The type of serializer to retrieve.

        Returns:
            BaseSerializer: An instance of the requested serializer.

        Raises:
            ValueError: If the specified type does not match any registered serializer.
        """

        if type not in cls.FACTORIES:
            raise ValueError("Incorrect serializer requested")

        _klass = cls.FACTORIES[type]

        return _klass(raw_data=raw_data, type=type)