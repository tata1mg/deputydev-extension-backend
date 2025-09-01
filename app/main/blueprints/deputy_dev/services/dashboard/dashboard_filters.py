from typing import Any, Dict, List, Optional

from sanic.log import logger

from app.backend_common.constants.constants import Connections
from app.backend_common.repository.db import DB
from app.backend_common.utils.sanic_wrapper import Task, TaskExecutor
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException, TaskExecutorException
from app.main.blueprints.deputy_dev.constants.dashboard_constants import (
    DashboardQueries,
    TileTypes,
)


class DashboardFiltersManager:
    """Manager class for handling dashboard filter operations and data fetching.

    This class provides methods to retrieve various dashboard-related data including
    teams, workspaces, repositories, pull requests, and dashboard tiles information.
    All methods interact with the database through raw SQL queries.
    """

    @classmethod
    async def get_teams(cls, query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fetch teams data for a given user.

        Args:
            query_params (dict): Dictionary containing query parameters.
                Required keys:
                - user_id: ID of the user to fetch teams for.

        Returns:
            list: List of teams data associated with the user.

        Raises:
            BadRequestException: If the database query fails.
        """
        query = DashboardQueries.teams_query.value

        try:
            data = await DB.raw_sql(query, connection=Connections.DEPUTY_DEV_REPLICA.value)
            return data
        except Exception as ex:  # noqa: BLE001
            logger.error(f"Failed to fetch teams data: {ex}")

    @classmethod
    async def get_workspaces(cls, query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fetch workspaces data for a given team.

        Args:
            query_params (dict): Dictionary containing query parameters.
                Required keys:
                - team_id: ID of the team to fetch workspaces for.

        Returns:
            list: List of workspaces data associated with the team.

        Raises:
            BadRequestException: If the database query fails.
        """
        team_id = query_params.get("team_id")
        if team_id is None:
            raise BadRequestException("Team ID must be provided to retrieve workspaces.")
        query = DashboardQueries.workspaces_query.value.format(team_id_condition=team_id)

        try:
            data = await DB.raw_sql(query, connection=Connections.DEPUTY_DEV_REPLICA.value)
            return data
        except Exception as ex:  # noqa: BLE001
            logger.error(f"Failed to fetch workspaces data for team_id={team_id}: {ex}")

    @classmethod
    async def get_repos(cls, query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fetch repositories data for a given workspace.

        Args:
            query_params (dict): Dictionary containing query parameters.
                Required keys:
                - workspace_id: ID of the workspace to fetch repositories for.

        Returns:
            list: List of repositories data associated with the workspace.

        Raises:
            BadRequestException: If the database query fails.
        """
        workspace_id = query_params.get("workspace_id")
        if workspace_id is None:
            raise BadRequestException("Workspace ID must be provided to retrieve repos.")
        query = DashboardQueries.repos_query.value.format(workspace_id_condition=workspace_id)

        try:
            data = await DB.raw_sql(query, connection=Connections.DEPUTY_DEV_REPLICA.value)
            return data
        except Exception as ex:  # noqa: BLE001
            logger.error(f"Failed to fetch repositories data for workspace_id={workspace_id}: {ex}")

    @classmethod
    async def get_prs(cls, query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fetch pull requests data based on specified filters.

        Args:
            bucket_type (str): Type of bucket to filter pull requests.
            start_date (str): Start date for the date range filter.
            end_date (str): End date for the date range filter.
            repo_ids (str): Comma-separated list of repository IDs.

        Returns:
            list: List of pull requests data matching the specified criteria.

        Raises:
            BadRequestException: If the database query fails.
        """
        # Extract from query params
        bucket_type = query_params.get("bucket_type")
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        repo_ids = query_params.get("repo_ids")
        limit = query_params.get("limit")
        offset = query_params.get("offset")

        query = DashboardQueries.pull_requests_query.value.format(
            bucket_type_condition=bucket_type,
            start_date=start_date,
            end_date=end_date,
            repo_ids=repo_ids,
            limit=limit,
            offset=offset,
        )
        try:
            data = await DB.raw_sql(query, connection=Connections.DEPUTY_DEV_REPLICA.value)
            return data
        except Exception as ex:  # noqa: BLE001
            logger.error(f"Failed to fetch pull requests data for bucket_type={bucket_type}: {ex}")

    @classmethod
    async def get_tiles(cls, query_params: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """
        Asynchronously retrieves tile data based on the provided query parameters.

        Args:
            query_params (dict): A dictionary containing the following keys:
                - "team_id" (str): Team identifier
                - "workspace_id" (str): Workspace identifier
                - "start_date" (str): The start date for filtering data.
                - "end_date" (str): The end date for filtering data.
                - "repo_ids" (list): A list of repository IDs to include in the query.

        Returns:
            dict: A dictionary containing the following keys:
                - "num_of_merged_prs" (int): The number of merged pull requests.
                - "num_of_raised_prs" (int): The number of raised pull requests.
                - "avg_code_review_time" (float): The average code review time in hours.
                - "merge_rate" (float or None): The merge rate as a percentage, or None if not calculable.

        Raises:
            BadRequestException: If an error occurs while processing the request or fetching data.
        """
        response = {}
        # Extract common parameters
        team_id = query_params.get("team_id")
        workspace_id = query_params.get("workspace_id")
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        repo_ids = query_params.get("repo_ids")

        try:
            queries = cls.get_tile_queries(start_date, end_date, repo_ids)

            # Define the tasks
            tasks = [
                Task(
                    DB.raw_sql(
                        queries.get(TileTypes.NUM_OF_MERGED_PRS.value), connection=Connections.DEPUTY_DEV_REPLICA.value
                    ),
                    result_key=TileTypes.NUM_OF_MERGED_PRS.value,
                ),
                Task(
                    DB.raw_sql(
                        queries.get(TileTypes.NUM_OF_RAISED_PRS.value), connection=Connections.DEPUTY_DEV_REPLICA.value
                    ),
                    result_key=TileTypes.NUM_OF_RAISED_PRS.value,
                ),
                Task(
                    DB.raw_sql(
                        queries.get(TileTypes.CODE_REVIEW_TIME.value), connection=Connections.DEPUTY_DEV_REPLICA.value
                    ),
                    result_key=TileTypes.CODE_REVIEW_TIME.value,
                ),
            ]

            # Create a TaskExecutor instance with the tasks and submit them
            executor = TaskExecutor(tasks=tasks)
            task_results = await executor.submit()

            for result in task_results:
                if isinstance(result.result, Exception):
                    logger.info(f"Exception while fetching task results, Details: {result.result}")
                else:
                    try:
                        # Map the result key to the response dictionary
                        if result.result_key == TileTypes.NUM_OF_MERGED_PRS.value:
                            response["num_of_merged_prs"] = result.result[0]["num_merged_prs"]
                        elif result.result_key == TileTypes.NUM_OF_RAISED_PRS.value:
                            response["num_of_raised_prs"] = result.result[0]["num_raised_prs"]
                        elif result.result_key == TileTypes.CODE_REVIEW_TIME.value:
                            response["avg_code_review_time"] = result.result[0]["avg_code_review_time_in_hours"]
                    except KeyError as ex:
                        logger.error(f"KeyError while processing result for {result.result_key}: {ex}")

            # Safely calculate merge rate
            if response.get("num_of_merged_prs") and response.get("num_of_raised_prs"):
                try:
                    merge_rate = round(response["num_of_merged_prs"] / response["num_of_raised_prs"] * 100, 1)
                    response["merge_rate"] = merge_rate
                except ZeroDivisionError:
                    logger.error("Division by zero while calculating merge rate")
                    response["merge_rate"] = None
        except TaskExecutorException as tex:
            raise TaskExecutorException(f"Failed to fetch tiles data with error: {tex}")
        except Exception as ex:  # noqa: BLE001
            logger.error(f"Failed to fetch tiles data for team_id={team_id} and workspace_id={workspace_id}: {ex}")

        return response

    @classmethod
    def get_tile_queries(cls, start_date: str, end_date: str, repo_ids: List[str]) -> Dict[str, str]:
        """
        Constructs SQL queries for retrieving tile data based on the provided parameters.

        Args:
            start_date (str): The start date for filtering data.
            end_date (str): The end date for filtering data.
            repo_ids (list): A list of repository IDs to include in the query.

        Returns:
            dict: A dictionary containing SQL queries for the following keys:
                - "num_of_merged_prs": SQL query for retrieving the number of merged pull requests.
                - "num_of_raised_prs": SQL query for retrieving the number of raised pull requests.
                - "code_review_time": SQL query for retrieving the average code review time.
        """

        queries = {
            "num_of_merged_prs": DashboardQueries.number_of_prs_merged_query.value.format(
                start_date=start_date, end_date=end_date, repo_ids=repo_ids
            ),
            "num_of_raised_prs": DashboardQueries.number_of_prs_raised_query.value.format(
                start_date=start_date, end_date=end_date, repo_ids=repo_ids
            ),
            "code_review_time": DashboardQueries.code_review_time_query.value.format(
                start_date=start_date, end_date=end_date, repo_ids=repo_ids
            ),
        }
        return queries
