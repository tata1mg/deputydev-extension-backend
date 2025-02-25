from typing import Any, Dict, List
from datetime import datetime

from app.backend_common.models.dto.message_sessions_dto import MessageSessionData
from app.main.blueprints.one_dev.services.serializer.base_serializers import BaseSerializer

class PastSessionsSerializer(BaseSerializer):
    def process_raw_data(self, raw_data: List[MessageSessionData], type: str) -> List[Dict[str, Any]]:
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
        age_in_minutes = (current_time - created_at).total_seconds() / 60
        if age_in_minutes < 60:
            return f"{int(age_in_minutes)}m"
        elif age_in_minutes < 1440:
            age_in_hours = age_in_minutes / 60
            return f"{int(age_in_hours)}h"
        else:
            age_in_days = age_in_minutes / 1440
            return f"{int(age_in_days)}d"