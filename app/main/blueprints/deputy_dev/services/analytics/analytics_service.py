from typing import Any, Dict

from sanic.log import logger

from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.main.blueprints.deputy_dev.constants.serializers_constants import (
    SerializerTypes,
)
from app.main.blueprints.deputy_dev.services.analytics.v1.analytics_factory import (
    AnalyticsFactory,
)
from app.main.blueprints.deputy_dev.services.dashboard.dashboard_filters import (
    DashboardFiltersManager,
)
from app.main.blueprints.deputy_dev.services.serializers.serializers_factory import (
    SerializersFactory,
)


class AnalyticsManager:
    """
    Manages analytics data processing and retrieval for dashboard visualizations.
    This class provides methods to handle analytics data requests, process raw data,
    and prepare it for visualization in various dashboard components.
    """

    @classmethod
    async def handle_analytics_data(cls, query_params: Dict[str, Any]) -> Dict[str, Any] | None:
        """Fetch and process analytics data based on query parameters.

        Args:
            query_params (dict): Query parameters containing:
                - team_id (str): Team identifier
                - workspace_id (str): Workspace identifier
                - repo_ids (list): List of repository IDs
                - graph_type (str): Type of graph to generate
                - interval_filter (str): Time interval for data aggregation
                - start_date (str): Start date for data range
                - end_date (str): End date for data range

        Returns:
            dict: Processed analytics data formatted for visualization

        Raises:
            BadRequestException: If analytics data request fails
        """
        team_id = query_params.get("team_id")
        workspace_id = query_params.get("workspace_id")
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        repo_ids = query_params.get("repo_ids")
        interval_filter = query_params.get("interval_filter")
        graph_type = query_params.get("graph_type")

        try:
            # Fetch analytics service
            analytics_service = AnalyticsFactory.get_analytics_service(
                start_date, end_date, repo_ids, graph_type, interval_filter
            )

            # Fetch raw analytics data
            raw_data = await analytics_service.get_analytics_data()

            # Process the raw data using the serializers factory
            serializer_service = SerializersFactory.get_serializer_service(
                raw_data, SerializerTypes.SHADCN.value, graph_type=graph_type, interval_filter=interval_filter
            )
            shadcn_service = serializer_service.get_shadcn_service()
            processed_data = shadcn_service.process_raw_data()

            return processed_data
        except ValueError as ve:
            raise BadRequestException(f"Value error occurred while fetching analytics data with error: {ve}")
        except TypeError as te:
            raise BadRequestException(f"Type error occurred while fetching analytics data with error: {te}")
        except Exception as ex:  # noqa: BLE001
            logger.error(f"Failed to fetch analytics data for team_id={team_id} and workspace_id={workspace_id}: {ex}")

    @classmethod
    async def handle_prs_data(cls, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch and process pull request data based on query parameters.

        Args:
            query_params (dict): Query parameters containing:
                - bucket_type (str): Type of bucket for data grouping
                - start_date (str): Start date for data range
                - end_date (str): End date for data range
                - repo_ids (list): List of repository IDs

        Returns:
            dict: Processed pull request data
        """

        raw_data = await DashboardFiltersManager.get_prs(query_params)

        serializer_service = SerializersFactory.get_serializer_service(
            raw_data, serializer_type=SerializerTypes.PRS_SERIALIZER.value
        )
        processed_data = serializer_service.process_raw_data()

        return processed_data
