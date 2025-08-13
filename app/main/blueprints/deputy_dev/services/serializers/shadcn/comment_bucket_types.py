from typing import Any, Dict, List

from app.main.blueprints.deputy_dev.services.serializers.shadcn.base_shadcn import (
    BaseShadcn,
)


class CommentBucketTypes(BaseShadcn):
    """
    A serializer class for processing raw comment data.

    This class inherits from the BaseShadcn and provides a specific implementation
    for processing raw data related to comment types.

    Attributes:
        raw_data: The raw input data that needs to be processed.
    """

    def process_raw_data(self) -> List[Dict[str, Any]]:
        """
        Process and return the raw data with formatted bucket types.

        Returns:
            The raw data with bucket types formatted.
        """
        formatted_data: List[Dict[str, Any]] = []
        for item in self.raw_data:
            formatted_item = item.copy()  # Copy the original item
            # Format the bucket_type
            # Removing the underscore and formatting it into title
            formatted_item["bucket_type"] = formatted_item["bucket_type"].replace("_", " ").title()
            formatted_data.append(formatted_item)
        return formatted_data
