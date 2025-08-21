from abc import ABC
from typing import Any, Dict, List


class BaseSerializers(ABC):
    """
    An abstract base class for serializers that process raw data
    based on a specific graph type.

    Attributes:
        raw_data (List[Dict[str, Any]]): The raw data to be processed.
        graph_type (str): The type of graph for which the data is being processed.
    """

    def __init__(self, raw_data: List[Dict[str, Any]], graph_type: str, interval_filter: str) -> None:
        self.raw_data = raw_data
        self.graph_type = graph_type
        self.interval_filter = interval_filter

    def get_processed_data(self) -> Any:
        """
        Retrieves the processed data by delegating to the `process_raw_data` method.

        Returns:
            Any: The processed data.

        Raises:
            NotImplementedError: If the `process_raw_data` method is not implemented in a subclass.
        """
        return self.process_raw_data(self.raw_data, self.graph_type, self.interval_filter)

    def process_raw_data(self, raw_data: List[Dict[str, Any]], graph_type: str, interval_filter: str) -> Any:
        """
        Processes the raw data based on the graph type.
        This method must be implemented by subclasses.

        Args:
            raw_data (List[Dict[str, Any]]): The raw data to be processed.
            graph_type (str): The type of graph for which the data is being processed.
            interval_filter (str): The interval filter for which the data is being processed.
        Returns:
            Any: The processed data.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement process raw data method")
