from app.main.blueprints.deputy_dev.constants.dashboard_constants import (
    AnalyticsDataQueries,
)

from .base_analytics import BaseAnalytics


class ReviewedVsRejected(BaseAnalytics):
    """Analytics class for generating data about reviewed vs rejected pull requests."""

    def __init__(
        self,
        start_date: str,
        end_date: str,
        repo_ids: str = None,
        graph_type: str = None,
        interval_filter: str = None,
    ) -> None:
        super().__init__(
            start_date=start_date,
            end_date=end_date,
            repo_ids=repo_ids,
            graph_type=graph_type,
            interval_filter=interval_filter,
        )
        self.graph_type = "reviewed_vs_rejected"

    def format_query(self) -> str:
        """
        Formats the SQL query to fetch data about comment types.

        Returns:
            str: SQL query string
        """
        base_query = AnalyticsDataQueries.reviewed_vs_rejected_query.value.format(
            start_date=self.start_date,
            end_date=self.end_date,
            interval_filter=self.interval_filter,
            repo_ids=self.repo_ids,
            interval_time=self.interval_filter.split()[1],
        )
        return base_query
