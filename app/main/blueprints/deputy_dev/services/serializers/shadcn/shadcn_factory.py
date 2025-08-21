from typing import Any, Dict, List, Type

from app.main.blueprints.deputy_dev.constants.dashboard_constants import GraphTypes
from app.main.blueprints.deputy_dev.services.serializers.base_serializers import (
    BaseSerializers,
)
from app.main.blueprints.deputy_dev.services.serializers.shadcn.base_shadcn import (
    BaseShadcn,
)
from app.main.blueprints.deputy_dev.services.serializers.shadcn.comment_bucket_types import (
    CommentBucketTypes,
)
from app.main.blueprints.deputy_dev.services.serializers.shadcn.pr_score import PrScore
from app.main.blueprints.deputy_dev.services.serializers.shadcn.reviewed_vs_rejected import (
    ReviewedVsRejected,
)


class ShadcnFactory(BaseSerializers):
    """
    A serializer factory class for processing Shadcn-based graph data.

    This class processes raw data for specific graph types by selecting the appropriate
    serializer class from the `FACTORIES` mapping. It ensures that the selected class
    inherits from `BaseShadcn` and returns the selected class

    Attributes:
        FACTORIES (Dict[str, Type[BaseShadcn]]): A mapping of graph types to their
            respective serializer classes.

    Methods:
        __init__(raw_data: List[Dict[str, Any]], graph_type: str, interval_filter: str): Initializes the Shadcn
            serializer with raw data, the graph type, and an interval filter.
        get_shadcn_service() -> An instance of the appropriate shadcn service.
    """

    FACTORIES: Dict[str, Type[BaseShadcn]] = {
        GraphTypes.COMMENT_BUCKET_TYPES.value: CommentBucketTypes,
        GraphTypes.PR_SCORE.value: PrScore,
        GraphTypes.REVIEWED_VS_REJECTED.value: ReviewedVsRejected,
    }

    def __init__(self, raw_data: List[Dict[str, Any]], graph_type: str, interval_filter: str) -> None:
        super().__init__(raw_data=raw_data, graph_type=graph_type, interval_filter=interval_filter)

    def get_shadcn_service(self) -> BaseShadcn:
        """
        Returns an instance of the shadcn service based on the provided graph type.

        Returns:
            An instance of the appropriate shadcn service.

        Raises:
            ValueError: If the specified graph type is invalid.
            TypeError: If the class associated with the graph type does not inherit from `BaseShadcn`.
        """
        if self.graph_type not in self.FACTORIES:
            raise ValueError("Invalid graph type for Shadcn")

        _klass = self.FACTORIES[self.graph_type]

        if not issubclass(_klass, BaseShadcn):
            raise TypeError("Graph type class must inherit from BaseShadcn")

        return _klass(self.raw_data, self.interval_filter)
