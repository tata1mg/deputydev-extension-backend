from typing import Any, Dict, List

from app.main.blueprints.deputy_dev.services.serializers.shadcn.base_shadcn import (
    BaseShadcn,
)


class PrScore(BaseShadcn):
    """
    A serializer for processing raw pull request (PR) score data.

    This class inherits from `BaseShadcn` and is responsible for transforming
    raw data into a structured format suitable for further analysis or visualization.

    Attributes:
        raw_data (list): A list of dictionaries, where each dictionary represents
        an entry containing a datetime `step` and a Decimal `pr_score`.

    Methods:
        process_raw_data():
            Converts raw PR score data into a list of dictionaries with
            formatted `step` (string) and `pr_score` (float) values.
    """

    def process_raw_data(self) -> List[Dict[str, Any]]:
        """
        Processes the raw data by converting datetime and Decimal values
        into their respective string and float formats.
        Maintains trend by carrying forward last non-zero PR score.

        Returns:
            list: A list of dictionaries containing:
                - `step` (str): The datetime in "YYYY-MM-DD HH:MM" format.
                - `pr_score` (float): The pull request score, maintaining last non-zero value.
        """
        if self.interval_filter == "1 hours":
            date_or_time_format = "%H:%M"
        else:
            date_or_time_format = "%Y-%m-%d"

        processed_data = []
        last_non_zero_score = 0

        for entry in self.raw_data:
            current_score = float(entry["pr_score"])
            # Update last_non_zero_score if current score is non-zero
            if current_score != 0:
                last_non_zero_score = current_score
            # Use last_non_zero_score if current is 0 (except for initial points)
            score_to_use = current_score if current_score != 0 or not processed_data else last_non_zero_score

            processed_data.append(
                {
                    "step": entry["step"].strftime(date_or_time_format),
                    "pr_score": score_to_use,
                }
            )

        return processed_data
