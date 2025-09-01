from __future__ import annotations

from ast import Tuple
from typing import Any, Dict, List

from deputydev_core.clients.http.adapters.http_response_adapter import AiohttpToRequestsAdapter
from deputydev_core.utils.app_logger import AppLogger
from sanic.log import logger

from app.backend_common.constants.constants import VCSFailureMessages
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.backend_common.utils.sanic_wrapper.exceptions import HTTPRequestException

from ..base_scm_client import BaseSCMClient


class BitbucketRepoClient(BaseSCMClient):
    """
    A class for interacting with Bitbucket API.
    """

    def __init__(self, workspace_slug: str, repo: str, pr_id: int, auth_handler: AuthHandler) -> None:
        self.workspace_slug = workspace_slug
        self.pr_id = pr_id
        self.repo = repo
        self.bitbucket_url = CONFIG.config["BITBUCKET"]["URL"]

        super().__init__(auth_handler=auth_handler)

    async def get_pr_details(self) -> Dict[str, Any] | None:
        """
        Get details of a pull request from Bitbucket.

        Returns:
            dict: pre details response
        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        diff_url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}"
        response = await self.get(diff_url)
        if response.status_code != 200:
            AppLogger.log_error(f"Unable to get PR details: error message {response._content}")
            return
        response_json = await response.json()
        return response_json

    async def update_pr_details(self, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        Update details of a pull request from Bitbucket.

        Returns:
            dict: pre details response
        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        diff_url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}"
        workspace_token_headers = await self.get_ws_token_headers()
        response = await self.put(diff_url, json=payload, headers=workspace_token_headers, skip_auth_headers=True)
        response_json = await response.json()
        if response.status_code == 200:
            return response_json
        elif (
            response.status_code == 400
            and response_json.get("error", {}).get("message") == VCSFailureMessages.BITBUCKET_PR_UPDATE_FAIL.value
        ):
            AppLogger.log_warn(f"PR couldn't updated due to not open {response_json}")
        else:
            AppLogger.log_error(f"PR couldn't updated {response_json}")

    async def get_pr_comments(self) -> List[Dict[str, Any]]:
        """
        Get all comments for the pull request, handling pagination.
        Note: In API response we get comments in ascending order of created_at
        Returns:
            list: List of all comments for the pull request.
        """
        comments: List[Dict[str, Any]] = []
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}/comments?pagelen=100"

        while url:
            response = await self.get(url)
            if response.status_code != 200:
                AppLogger.log_warn(f"Error fetching comments: {response.status_code}, {response.text}")
                return comments
            data = await response.json()
            comments.extend(data.get("values", []))
            # next is none incase there are no more comments and while loop breaks
            url = data.get("next")

        return comments

    async def get_pr_diff(self) -> Tuple[AiohttpToRequestsAdapter, int]:
        """
        Get the diff of a pull request from Bitbucket.

        Returns:
            str: The diff of the pull request.
        """
        diff_url = (
            f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}/diff"
        )
        response = await self.get(diff_url)
        if response.status_code not in [200, 404]:
            error_msg = f"Unable to retrieve diff for PR - {self.pr_id}: {response._content}"
            raise HTTPRequestException(status_code=response.status_code, error=error_msg)
        return response, response.status_code

    async def get_commit_diff(self, base_commit: str, destination_commit: str) -> Tuple[AiohttpToRequestsAdapter, int]:
        """
        Get the diff between two commits in Bitbucket.

        Args:
            base_commit (str): The base commit hash.
            destination_commit (str): The destination commit hash.

        Returns:
            str: The diff between the two commits.
        """
        diff_url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/diff/{base_commit}..{destination_commit}"
        response = await self.get(diff_url)
        if response.status_code not in [200, 404]:
            error_msg = f"Unable to retrieve diff for PR - {self.pr_id}: {response._content}"
            raise HTTPRequestException(status_code=response.status_code, error=error_msg)
        return response, response.status_code

    async def create_comment_on_pr(self, comment: Dict[str, Any], model: str) -> AiohttpToRequestsAdapter | None:
        """
        Create a comment on the pull request.

        Parameters:
        - comment (str): The content of the comment.
        - model(str): model which was used to receive comment. Helps identify the bot to post comment

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        workspace_token_headers = await self.get_ws_token_headers()
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}/comments"
        response = await self.post(url, json=comment, headers=workspace_token_headers, skip_auth_headers=True)
        return response

    async def get_comment_details(self, comment_id: str) -> AiohttpToRequestsAdapter | None:
        """
        Get the comment details on PR from Bitbucket.

        Returns:
            Dict: Comment Details

        Raises:
            ValueError: If the diff cannot be retrieved.
        """
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}/comments/{comment_id}"
        response = await self.get(url)
        if response.status_code != 200:
            logger.error(
                f"Unable to retrieve Comment details for comment: {comment_id} - PR ID: {self.pr_id}: {response._content}"
            )
        return response

    async def get_pr_diff_stats(self) -> AiohttpToRequestsAdapter | None:
        """
        Get the diff stat of pull request

        Returns:
            str: The diff of the pull request.
        """
        diff_url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}/diffstat/"
        response = await self.get(diff_url)
        if response.status_code != 200:
            AppLogger.log_error(f"Unable to retrieve diffstats for PR Response: {response._content}")
            return None
        return response

    async def get_commit_diff_stats(self, base_commit: str, destination_commit: str) -> AiohttpToRequestsAdapter | None:
        """
        Get the diff stat between two commits

        Returns:
            str: The diff of the pull request.
        """
        diff_url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/diffstat/{base_commit}..{destination_commit}"
        response = await self.get(diff_url)
        if response.status_code != 200:
            AppLogger.log_error(f"Unable to retrieve commit diffstats for PR Response: {response._content}")
            return None
        return response

    async def fetch_diffstat(self, repo_name: str, scm_pr_id: str) -> int:
        url = "https://api.bitbucket.org/2.0/repositories/tata1mg/{repo_name}/pullrequests/{scm_pr_id}/diffstat".format(
            repo_name=repo_name, scm_pr_id=scm_pr_id
        )
        response = await self.get(url)
        if response.status_code == 200:
            data = await response.json()
            return sum(file["lines_added"] + file["lines_removed"] for file in data["values"])
        else:
            return 0

    async def get_pr_diff_v1(self, repo_name: str, scm_pr_id: str) -> Tuple[AiohttpToRequestsAdapter, int]:
        """
        Get the diff of a pull request from Bitbucket.

        Returns:
            str: The diff of the pull request.
        """
        diff_url = (
            "https://api.bitbucket.org/2.0/repositories/tata1mg/{repo_name}/pullrequests/{scm_pr_id}/diff".format(
                repo_name=repo_name, scm_pr_id=scm_pr_id
            )
        )
        response = await self.get(diff_url)
        if response.status_code != 200:
            AppLogger.log_error(f"Unable to retrieve diff for PR - {self.pr_id}: {response._content}")
        return response, response.status_code

    async def get_pr_commits(self) -> List[Any]:
        """Get all commits in a Bitbucket PR with pagination"""
        url = (
            f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests/{self.pr_id}/commits"
        )

        response = await self.get(url, params={"pagelen": 100})

        if response and response.status_code == 200:
            response_json = await response.json()
            return response_json.get("values", [])

        AppLogger.log_error(
            f"Unable to retrieve commits and hence PR is reviewed with full diff - {self.pr_id}: {response._content}"
        )
        return []

    async def create_pr(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a PR on Bitbucket.

        Returns:
            dict: PR creation response
        """
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests"
        workspace_token_headers = await self.get_ws_token_headers()
        response = await self.post(url, json=payload, headers=workspace_token_headers, skip_auth_headers=True)
        return await response.json()

    async def list_prs(self, state: str = "OPEN") -> Dict[str, Any]:
        """
        List all PRs on Bitbucket.

        Returns:
            dict: PR list response
        """
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/pullrequests"
        response = await self.get(url, params={"state": state})
        return await response.json()

    async def create_issue_comment(self, issue_id: str, comment: str) -> Dict[str, Any]:
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/issues/{issue_id}/comments"
        payload = {"content": {"raw": comment}}
        response = await self.post(url, json=payload)
        return await response.json()

    async def get_file(self, branch_name: str, file_path: str) -> AiohttpToRequestsAdapter:
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace_slug}/{self.repo}/src/{branch_name}/{file_path}"
        response = await self.get(url)
        if response.status_code != 200:
            return None
        return response
