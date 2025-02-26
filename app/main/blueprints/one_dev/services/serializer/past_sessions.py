from typing import Any, Dict, List
from datetime import datetime

from app.backend_common.models.dto.message_sessions_dto import MessageSessionData
from app.main.blueprints.one_dev.services.serializer.base_serializers import BaseSerializer

class PastSessionsSerializer(BaseSerializer):
    """
    Serializer for processing past message sessions data.

    Inherits from BaseSerializer and implements the method to format raw message session data.
    """

    def process_raw_data(self, raw_data: List[MessageSessionData], type: str) -> List[Dict[str, Any]]:
        """
        Processes raw message session data and formats it for output.

        Args:
            raw_data (List[MessageSessionData]): The raw message session data to be processed.
            type (str): The type of data being serialized.

        Returns:
            List[Dict[str, Any]]: A list of formatted message session data.
        """
        formatted_data = []
        current_time = datetime.now()
        for item in raw_data[::-1]:
            formatted_data.append(
                {
                    "id": item.id,
                    "summary": item.summary,
                    "age": self.calculate_age(current_time, item.created_at),
                }
            )
        return formatted_data

    def calculate_age(self, current_time: datetime, created_at: datetime) -> str:
        """
        Calculates the age of a message session based on the current time and its creation time.

        Args:
            current_time (datetime): The current time.
            created_at (datetime): The creation time of the message session.

        Returns:
            str: A string representing the age in minutes, hours, or days.
        """
        age_in_minutes = (current_time - created_at).total_seconds() / 60
        if age_in_minutes < 60:
            return f"{int(age_in_minutes)}m"
        elif age_in_minutes < 1440:
            age_in_hours = age_in_minutes / 60
            return f"{int(age_in_hours)}h"
        else:
            age_in_days = age_in_minutes / 1440
            return f"{int(age_in_days)}d"