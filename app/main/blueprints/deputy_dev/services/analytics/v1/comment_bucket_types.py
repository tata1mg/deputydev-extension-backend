from app.main.blueprints.deputy_dev.constants.dashboard_constants import (
    AnalyticsDataQueries,
)

from .base_analytics import BaseAnalytics


class CommentBucketTypes(BaseAnalytics):
    """Analytics class for generating data about comment types."""

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
        self.graph_type = "comment_types"

    def format_query(self) -> str:
        """
        Formats the SQL query to fetch data about comment types.

        Returns:
            str: SQL query string
        """
        base_query = AnalyticsDataQueries.comment_bucket_types_query.value.format(
            start_date=self.start_date,
            end_date=self.end_date,
            repo_ids=self.repo_ids,
        )

        return base_query
