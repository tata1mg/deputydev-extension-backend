from typing import Dict, Type

from app.main.blueprints.deputy_dev.constants.dashboard_constants import GraphTypes
from app.main.blueprints.deputy_dev.services.analytics.v1.base_analytics import BaseAnalytics
from app.main.blueprints.deputy_dev.services.analytics.v1.comment_bucket_types import (
    CommentBucketTypes,
)
from app.main.blueprints.deputy_dev.services.analytics.v1.pr_score import PrScore
from app.main.blueprints.deputy_dev.services.analytics.v1.reviewed_vs_rejected import (
    ReviewedVsRejected,
)


class AnalyticsFactory:
    """Factory class to get an instance of the analytics service based on the graph type"""

    FACTORIES: Dict[str, Type[BaseAnalytics]] = {
        GraphTypes.COMMENT_BUCKET_TYPES.value: CommentBucketTypes,
        GraphTypes.PR_SCORE.value: PrScore,
        GraphTypes.REVIEWED_VS_REJECTED.value: ReviewedVsRejected,
    }

    @classmethod
    def get_analytics_service(
        cls, start_date: str, end_date: str, repo_ids: str, graph_type: str, interval_filter: str
    ) -> BaseAnalytics:
        """
        Returns an instance of the analytics service based on the provided graph type.

        Args:
            start_date (str): Start date for the data.
            end_date (str): End date for the data.
            repo_ids (str): IDs of the repos.
            graph_type (str): Graph type of data to generate.
            interval_filter (str): Time interval filter for the data.

        Returns:
            An instance of the appropriate analytics service.

        Raises:
            ValueError: If an incorrect graph type is requested.
        """
        if graph_type not in cls.FACTORIES:
            raise ValueError("Incorrect graph requested")
        return cls.FACTORIES[graph_type](
            start_date=start_date,
            end_date=end_date,
            repo_ids=repo_ids,
            graph_type=graph_type,
            interval_filter=interval_filter,
        )
