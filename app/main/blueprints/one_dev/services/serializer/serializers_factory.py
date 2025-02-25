from app.main.blueprints.one_dev.constants.serializers_constants import SerializerTypes
from app.main.blueprints.one_dev.services.serializer.base_serializers import BaseSerializer
from typing import Any, Dict, List

from app.main.blueprints.one_dev.services.serializer.past_chats import PastChatsSerializer
from app.main.blueprints.one_dev.services.serializer.past_sessions import PastSessionsSerializer

class SerializersFactory:

    FACTORIES = {
        SerializerTypes.PAST_SESSIONS.value: PastSessionsSerializer,
        SerializerTypes.PAST_CHATS.value: PastChatsSerializer
    }

    @classmethod
    def get_serializer_service(cls, raw_data: List[Dict[str, Any]], type: str) -> BaseSerializer:

        if type not in cls.FACTORIES:
            raise ValueError("Incorrect serializer requested")

        _klass = cls.FACTORIES[type]

        return _klass(raw_data=raw_data, type=type)