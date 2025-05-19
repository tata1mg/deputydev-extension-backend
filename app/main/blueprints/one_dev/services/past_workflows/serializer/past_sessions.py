from datetime import datetime
from typing import Any, Dict, List

from app.backend_common.models.dto.extension_sessions_dto import ExtensionSessionDTO
from app.main.blueprints.one_dev.services.past_workflows.constants.serializer_constants import (
    SerializerTypes,
)
from app.main.blueprints.one_dev.services.past_workflows.serializer.base_serializers import (
    BaseSerializer,
)


class PastSessionsSerializer(BaseSerializer):
    """
    Serializer for processing past message sessions data.

    Inherits from BaseSerializer and implements the method to format raw message session data.
    """

    async def process_raw_data(self, raw_data: List[ExtensionSessionDTO], type: SerializerTypes) -> List[Dict[str, Any]]:
        """
        Processes raw message session data and formats it for output.

        Args:
            raw_data (List[ExtensionSessionDTO]): The raw message session data to be processed.
            type (SerializerTypes): The type of data being serialized.

        Returns:
            List[Dict[str, Any]]: A list of formatted message session data.
        """
        formatted_data: List[Dict[str, Any]] = []
        current_time = datetime.now()
        for item in raw_data:
            if item.summary:
                formatted_data.append(
                    {
                        "id": item.session_id,
                        "summary": item.summary,
                        "age": self.calculate_age(current_time, item.updated_at),
                        "pinned_rank": item.pinned_rank,
                        "created_at": item.created_at.isoformat(),
                        "updated_at": item.updated_at.isoformat(),
                    }
                )
        return formatted_data

    def calculate_age(self, current_time: datetime, updated_at: datetime) -> str:
        """
        Calculates the age of a message session based on the current time and its creation time.

        Args:
            current_time (datetime): The current time.
            updated_at (datetime): The creation time of the message session.

        Returns:
            str: A string representing the age in minutes, hours, or days.
        """
        age_in_seconds = (current_time - updated_at).total_seconds()
        if age_in_seconds < 60:
            return f"{int(age_in_seconds)}s"
        elif age_in_seconds < 3600:
            age_in_minutes = age_in_seconds / 60
            return f"{int(age_in_minutes)}m"
        elif age_in_seconds < 86400:
            age_in_hours = age_in_seconds / 3600
            return f"{int(age_in_hours)}h"
        else:
            age_in_days = age_in_seconds / 86400
            return f"{int(age_in_days)}d"
