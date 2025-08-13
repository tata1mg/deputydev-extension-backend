from abc import ABC
from typing import Any, Dict, List


class BaseShadcn(ABC):
    """
    Abstract base class for processing raw data in the Shadcn serializer factory.

    Attributes:
        raw_data (List[Dict[str, Any]]): A list of dictionaries containing raw input data.
        interval_filter (str): The interval filter for the data.
    """

    def __init__(self, raw_data: List[Dict[str, Any]], interval_filter: str) -> None:
        self.raw_data = raw_data
        self.interval_filter = interval_filter

    def process_raw_data(self) -> List[Dict[str, Any]]:
        """
        Abstract method to process raw data.

        Subclasses must override this method to define specific data processing logic.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement the process_raw_data method")
