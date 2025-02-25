from abc import ABC
from typing import Any, Dict, List

class BaseSerializer(ABC):

   def __init__(self, raw_data: List[Dict[str, Any]], type: str):
      self.raw_data = raw_data
      self.type = type

   def get_processed_data(self) -> List[Dict[str, Any]]:
      return self.process_raw_data(self.raw_data, self.type)

   def process_raw_data(self, raw_data: List[Dict[str, Any]], type: str) -> List[Dict[str, Any]]:
      raise NotImplementedError("Subclasses must implement process raw data method")
