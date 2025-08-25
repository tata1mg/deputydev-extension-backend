from collections import defaultdict
from typing import Any, Dict, List

from app.main.blueprints.deputy_dev.constants.constants import REJECTED_STATUS_TYPES
from app.main.blueprints.deputy_dev.services.serializers.shadcn.base_shadcn import (
    BaseShadcn,
)


class ReviewedVsRejected(BaseShadcn):
    """
    A serializer class for processing raw data to generate statistics
    about reviewed and rejected items over time.

    The raw data is expected to contain entries with the following keys:
    - 'step': A datetime object representing the date of the entry.
    - 'count': An integer representing the count of items for the entry.
    - 'review_status': A string representing the review status of the entry.

    This class aggregates the data by date and calculates:
    - Total reviewed counts
    - Total rejected counts

    Methods:
        process_raw_data: Processes and aggregates the raw data to produce
                          a list of dictionaries with date-wise reviewed
                          and rejected totals.
    """

    def process_raw_data(self) -> List[Dict[str, Any]]:
        """
        Method to process raw data and aggregate statistics using defaultdict.

        Returns:
            list: A list of dictionaries with date-wise reviewed and rejected totals.
                  Example:
                  [
                      {
                          "date": "2024-11-19",
                          "total_reviewed": 10,
                          "total_rejected": 5
                      },
                      ...
                  ]
        """
        # Determine the date or time format based on the interval filter
        date_or_time_format = "%H:%M" if self.interval_filter == "1 hours" else "%Y-%m-%d"

        # Initialize a defaultdict to accumulate totals
        aggregated_data = defaultdict(lambda: {"total_reviewed": 0, "total_rejected": 0})

        for entry in self.raw_data:
            # Format the date or time according to the specified format
            formatted_date = entry["step"].strftime(date_or_time_format)
            count = entry["count"]
            review_status = entry["review_status"]

            # Update the counts based on the review status
            if review_status in REJECTED_STATUS_TYPES:
                aggregated_data[formatted_date]["total_rejected"] += count
            else:
                aggregated_data[formatted_date]["total_reviewed"] += count

        # Convert the aggregated data to a list of dictionaries
        return [
            {
                "date": date,
                "total_reviewed": counts["total_reviewed"],
                "total_rejected": counts["total_rejected"],
            }
            for date, counts in aggregated_data.items()
        ]
