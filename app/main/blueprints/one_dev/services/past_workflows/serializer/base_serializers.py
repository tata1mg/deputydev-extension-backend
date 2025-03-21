from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.main.blueprints.one_dev.services.past_workflows.constants.serializer_constants import (
    SerializerTypes,
)


class BaseSerializer(ABC):
    """
    A base class for serializing raw data.

    Attributes:
       raw_data (List[Dict[str, Any]]): The raw data to be processed.
       type (SerializerTypes): The type of data being serialized.
    """

    def __init__(self, raw_data: List[Dict[str, Any]], type: SerializerTypes):
        """
        Initializes the BaseSerializer with raw data and type.

        Args:
           raw_data (List[Dict[str, Any]]): The raw data to be serialized.
           type (SerializerTypes): The type of data being serialized.
        """

        self.raw_data = raw_data
        self.type = type

    def get_processed_data(self) -> List[Dict[str, Any]]:
        """
        Processes the raw data and returns the serialized output.

        Returns:
           List[Dict[str, Any]]: The processed data.
        """

        return self.process_raw_data(self.raw_data, self.type)

    @abstractmethod
    def process_raw_data(self, raw_data: List[Dict[str, Any]], type: SerializerTypes) -> List[Dict[str, Any]]:
        """
        Abstract method to process raw data. Must be implemented by subclasses.

        Args:
           raw_data (List[Dict[str, Any]]): The raw data to be processed.
           type (SerializerTypes): The type of data being serialized.

        Raises:
           NotImplementedError: If not implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process raw data method")
