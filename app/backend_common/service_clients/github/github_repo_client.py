from typing import Any, Dict, List, Optional

from deputydev_core.clients.http.adapters.http_response_adapter import AiohttpToRequestsAdapter
from deputydev_core.utils.app_logger import AppLogger
from sanic.log import logger

from app.backend_common.constants.constants import VCSFailureMessages
from app.backend_common.service_clients.base_scm_client import BaseSCMClient
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.backend_common.utils.sanic_wrapper.exceptions import HTTPRequestException

config = CONFIG.config


class GithubRepoClient(BaseSCMClient):
    """
    class handles rest api calls for Github PR reviews
    """

    def __init__(self, workspace_slug: str, repo: str, pr_id: int, auth_handler: AuthHandler) -> None:
        self.workspace_slug = workspace_slug
        self.pr_id = pr_id
        self.repo = repo

        super().__init__(auth_handler=auth_handler)

    HOST = config["GITHUB"]["HOST"]

    async def create_pr_comment(self, payload: Dict[str, Any]) -> AiohttpToRequestsAdapter | None:
        """
        creates comment on whole PR
        """
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/issues/{self.pr_id}/comments"
        try:
            result = await self.post(url=path, json=payload)
            return result
        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"unable to comment on github pr for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} err {ex}"
            )

    async def create_issue_comment(self, payload: Dict[str, Any], issue_id: int) -> AiohttpToRequestsAdapter | None:
        """Create a comment on PR conversation/issue tab"""
        url = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/issues/{issue_id}/comments"
        return await self.post(url=url, json=payload)

    async def update_pr(
        self, payload: Dict[str, Any], headers: Dict[str, str] | None = None
    ) -> AiohttpToRequestsAdapter | None:
        """
        Updates PR properties like description
        """
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/issues/{self.pr_id}"
        try:
            result = await self.patch(path, json=payload, headers=headers)
            return result
        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"unable to  update pr for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} err {ex}"
            )

    async def create_pr_review_comment(
        self, payload: Dict[str, Any], headers: Dict[str, str] | None = None
    ) -> Optional[AiohttpToRequestsAdapter]:
        """
        Creates pr review comment on a file and line
        """
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}/comments"
        try:
            result = await self.post(url=path, json=payload, headers=headers)
            result_json = await result.json()
            if result.status_code == 201:
                return result
            elif result.status_code == 422:
                if (
                    result_json.get("message") == VCSFailureMessages.GITHUB_VALIDATION_FAIL.value
                    and result_json.get("errors", [{}])[0].get("field")
                    == VCSFailureMessages.GITHUB_INCORRECT_LINE_NUMBER.value
                ):
                    AppLogger.log_warn(
                        f"Unable to create comment on pr due to invalid line - {result.status_code} {result_json}"
                    )
                if (
                    result_json.get("message") == VCSFailureMessages.GITHUB_VALIDATION_FAIL.value
                    and result_json.get("errors", [{}])[0].get("field")
                    == VCSFailureMessages.GITHUB_INCORRECT_FILE_PATH.value
                ):
                    AppLogger.log_warn(
                        f"Unable to create comment on pr due to invalid path - {result.status_code} {result_json}"
                    )
            else:
                AppLogger.log_error(f"Unable to create comment on pr - {result.status_code} {result_json}")
            return result
        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"unable to comment on github pr for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} err {ex}"
            )

    async def get_pr_diff(self) -> Optional[AiohttpToRequestsAdapter]:
        """
        returns pr diff in git format
        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}"
        headers["Accept"] = "application/vnd.github.v3.diff"

        result = await self.get(path, headers=headers)
        if result.status_code not in [200, 404, 406]:
            error_msg = f"Unable to retrieve diff for PR - {self.pr_id}: {result._content}"
            raise HTTPRequestException(status_code=result.status_code, error=error_msg)
        return result

    async def get_commit_diff(self, commit_a: str, commit_b: str) -> Optional[AiohttpToRequestsAdapter]:
        """
        Get the diff between two commits in GitHub.

        Args:
            commit_a (str): The first commit hash.
            commit_b (str): The second commit hash.

        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/compare/{commit_b}...{commit_a}"
        headers["Accept"] = "application/vnd.github.v3.diff"

        result = await self.get(path, headers=headers)
        if result.status_code not in [200, 404]:
            error_msg = f"Unable to retrieve diff for PR - {self.pr_id}: {result._content}"
            raise HTTPRequestException(status_code=result.status_code, error=error_msg)
        return result

    async def get_pr_details(self) -> Optional[AiohttpToRequestsAdapter]:
        """
        returns pr details
        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}"
        headers["Accept"] = "application/vnd.github+json"
        try:
            result = await self.get(path, headers=headers)
            return result
        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"unable to get github pr details for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} er {ex}"
            )

    async def get_comment_thread(
        self, user_name: str, repo_name: str, comment_id: str, headers: Dict[str, str] | None = None
    ) -> Optional[AiohttpToRequestsAdapter]:
        """
        returns comment thread
        """
        headers = headers or {}
        path = f"{self.HOST}/repos/{user_name}/{repo_name}/pulls/comments/{comment_id}"
        headers["Accept"] = "application/vnd.github+json"
        try:
            result = await self.get(path, headers=headers)
            return result
        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"unable to get github comment thread details for repo_name: {repo_name}, "
                f"comment_id: {comment_id}, user_name: {user_name} er {ex}"
            )

    async def get_pr_diff_stats(self, headers: Dict[str, str] | None = None) -> Optional[AiohttpToRequestsAdapter]:
        """
        Get the diff stat of a pull request from GitHub.

        Returns:
            aiohttp.ClientResponse: The response object containing the diff stats of the pull request.
        """
        headers = headers or {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}/files"
        headers["Accept"] = "application/vnd.github+json"

        response = await self.get(path, headers=headers)
        if response.status_code != 200:
            AppLogger.log_error(f"Unable to retrieve diff for PR - {response.status_code}")
            return None
        return response

    async def get_commit_diff_stats(
        self, base_commit: str, destination_commit: str, headers: Dict[str, str] | None = None
    ) -> Optional[AiohttpToRequestsAdapter]:
        """
        Get the diff stat between two commits

        Returns:
            str: The diff of the pull request.
        """
        headers = headers or {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/compare/{destination_commit}...{base_commit}"
        headers["Accept"] = "application/vnd.github+json"

        response = await self.get(path, headers=headers)
        if response.status_code != 200:
            AppLogger.log_error(f"Unable to retrieve diff for PR - {response.status_code}")
            return None
        return response

    async def update_pr_details(self, payload: Dict[str, Any]) -> Optional[AiohttpToRequestsAdapter]:
        """
        Update the details of a pull request on GitHub.

        Args:
            payload (dict): The payload containing updated details (like description).

        Returns:
            dict: Response containing the updated pull request details.
        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}"
        headers["Accept"] = "application/vnd.github+json"

        response = await self.patch(path, headers=headers, json=payload)
        if response.status_code == 200:
            return await response.json()
        else:
            error_json = await response.json()
            AppLogger.log_error("PR couldn't updated {}".format(error_json))

    async def get_pr_commits(self) -> List[Dict[str, Any]]:
        """
        Get the latest commit SHA of a pull request on GitHub.

        Returns:
            dict: Response containing the latest commit SHA.
        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}/commits"
        headers["Accept"] = "application/vnd.github+json"
        commits = []

        params = {"per_page": 100, "page": 1}  # Maximum page size for GitHub

        while True:
            response = await self.get(path, params=params, headers=headers)
            if not response or response.status_code != 200:
                AppLogger.log_error(
                    f"Unable to retrieve commits and hence PR is reviewed with full diff - {self.pr_id}: {response._content}"
                )
                break

            data = await response.json()
            if not data:
                break

            commits.extend(data)

            # Check if we've received less than the maximum items per page
            if len(data) < params["per_page"]:
                break

            params["page"] += 1

        return list(reversed(commits))

    async def get_pr_comments(self) -> List[Dict[str, Any]]:
        """
        Get all the comments on a PR in GitHub.
        Note: In API response we get comments in ascending order of created_at
        Returns:
            dict: List of comments in PR.
        """
        headers = {}
        comments = []

        # Set headers for authorization and content type
        headers["Accept"] = "application/vnd.github+json"

        page = 1
        while True:
            path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}/comments?page={page}&per_page=100"
            response = await self.get(path, headers=headers)
            if response.status_code != 200:
                AppLogger.log_warn(f"Error fetching comments: {response.status_code}, {response.text}")
                return comments
            data = await response.json()
            # Returns empty list incase we pass page with no comments
            if not data:
                break
            comments.extend(data)
            page += 1
        return comments

    async def get_file(self, branch_name: str, file_path: str) -> Optional[bytes]:
        url = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/contents/{file_path}?ref={branch_name}"
        response = await self.get(url)
        if response.status_code != 200:
            return None
        return response.content

    async def create_pr(self, payload: Dict[str, Any], headers: Dict[str, str] | None = None) -> Dict[str, Any]:
        """
        Create a PR on Github.

        Returns:
            dict: PR creation response
        """
        headers = headers or {}
        headers["Accept"] = "application/vnd.github+json"
        url = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls"
        response = await self.post(url, json=payload, headers=headers)
        return await response.json()

    async def list_prs(
        self, state: str = "open", source: str | None = None, destination: str | None = None
    ) -> Dict[str, Any]:
        """
        List all PRs on github.

        Returns:
            dict: PR list response
        """
        url = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls"
        response = await self.get(
            url, params={"state": state, "head": f"{self.workspace_slug}:{source}", "base": destination}
        )
        return await response.json()
