from typing import Any, Dict, List

from app.main.blueprints.deputy_dev.constants.serializers_constants import (
    SerializerTypes,
)
from app.main.blueprints.deputy_dev.services.serializers.base_serializers import (
    BaseSerializers,
)
from app.main.blueprints.deputy_dev.services.serializers.pull_requests.prs_serializer import (
    PrsSerializer,
)
from app.main.blueprints.deputy_dev.services.serializers.shadcn.shadcn_factory import (
    ShadcnFactory,
)


class SerializersFactory:
    FACTORIES = {
        SerializerTypes.SHADCN.value: ShadcnFactory,
    }

    @classmethod
    def get_serializer_service(
        cls, raw_data: List[Dict[str, Any]], serializer_type: str, graph_type: str = None, interval_filter: str = None
    ) -> BaseSerializers:
        """
        Returns an instance of the serializer service based on the provided serializer type.

        Args:
            raw_data (List[Dict[str, Any]]): The raw data to be processed.
            serializer_type (str): The type of serializer to use.
            graph_type (str, optional): The type of graph for which data is being processed.
                                      Required for some serializers, optional for others.

        Returns:
            An instance of the appropriate serializer service.

        Raises:
            ValueError: If an incorrect serializer type is requested.
        """
        if serializer_type == SerializerTypes.PRS_SERIALIZER.value:
            return PrsSerializer(raw_data=raw_data)
        if serializer_type not in cls.FACTORIES:
            raise ValueError("Incorrect serializer requested")
        return cls.FACTORIES[serializer_type](raw_data=raw_data, graph_type=graph_type, interval_filter=interval_filter)
