from typing import Optional

from sanic.log import logger
from torpedo import CONFIG

from app.common.constants.constants import VCSFailureMessages
from app.common.service_clients.base_scm_client import BaseSCMClient
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler

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

    async def create_pr_comment(self, payload: dict):
        """
        creates comment on whole PR
        """
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/issues/{self.pr_id}/comments"
        try:
            result = await self.post(url=path, json=payload)
            return result
        except Exception as ex:
            logger.error(
                f"unable to comment on github pr for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} err {ex}"
            )

    async def update_pr(self, payload: dict, headers: dict = None):
        """
        Updates PR properties like description
        """
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/issues/{self.pr_id}"
        try:
            result = await self.patch(path, json=payload, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to  update pr for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} err {ex}"
            )

    async def create_pr_review_comment(self, payload: dict, headers: dict = None):
        """
        Creates pr review comment on a file and line
        """
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}/comments"
        try:
            result = await self.post(url=path, json=payload, headers=headers)
            if result.status_code == 201:
                return result
            elif result.status_code == 422:
                if (
                    result.json().get("message") == VCSFailureMessages.GITHUB_VALIDATION_FAIL.value
                    and result.json().get("errors", [{}])[0].get("field")
                    == VCSFailureMessages.GITHUB_INCORRECT_LINE_NUMBER.value
                ):
                    AppLogger.log_warn(
                        f"Unable to create comment on pr due to invalid line - {result.status_code} {result.json()}"
                    )
                if (
                    result.json().get("message") == VCSFailureMessages.GITHUB_VALIDATION_FAIL.value
                    and result.json().get("errors", [{}])[0].get("field")
                    == VCSFailureMessages.GITHUB_INCORRECT_FILE_PATH.value
                ):
                    AppLogger.log_warn(
                        f"Unable to create comment on pr due to invalid path - {result.status_code} {result.json()}"
                    )
            else:
                AppLogger.log_error(f"Unable to create comment on pr - {result.status_code} {result.json()}")
            return result
        except Exception as ex:
            logger.error(
                f"unable to comment on github pr for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} err {ex}"
            )

    async def get_pr_diff(self):
        """
        returns pr diff in git format
        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}"
        headers["Accept"] = "application/vnd.github.v3.diff"
        try:
            result = await self.get(path, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to get github pr diff for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} err {ex}"
            )

    async def get_pr_details(self, headers=None):
        """
        returns pr details
        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}"
        headers["Accept"] = "application/vnd.github+json"
        try:
            result = await self.get(path, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to get github pr details for repo_name: {self.repo}, "
                f"pr_id: {self.pr_id}, user_name: {self.workspace_slug} er {ex}"
            )

    async def get_comment_thread(self, user_name, repo_name, comment_id, headers=None):
        """
        returns comment thread
        """
        headers = headers or {}
        path = f"{self.HOST}/repos/{user_name}/{repo_name}/pulls/comments/{comment_id}"
        headers["Accept"] = "application/vnd.github+json"
        try:
            result = await self.get(path, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to get github comment thread details for repo_name: {repo_name}, "
                f"comment_id: {comment_id}, user_name: {user_name} er {ex}"
            )

    async def get_pr_diff_stats(self, headers=None):
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

    async def update_pr_details(self, payload) -> Optional[dict]:
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
            return response.json()
        else:
            AppLogger.log_error("PR couldn't updated {}".format(response.json()))

    async def get_pr_commits(self) -> dict:
        """
        Get the latest commit SHA of a pull request on GitHub.

        Args:
            user_name (str): The owner of the repository.
            repo_name (str): The name of the repository.
            pr_id (int): The ID number of the pull request.
            headers (dict, optional): Additional headers to pass in the request.

        Returns:
            dict: Response containing the latest commit SHA.
        """
        headers = {}
        path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}/commits"
        headers["Accept"] = "application/vnd.github+json"

        response = await self.get(path, headers=headers)

        return response.json()

    async def get_pr_comments(self) -> list:
        """
        Get the latest commit SHA of a pull request on GitHub.

        Args:
            user_name (str): The owner of the repository.
            repo_name (str): The name of the repository.
            pr_id (int): The ID number of the pull request.
            headers (dict, optional): Additional headers to pass in the request.

        Returns:
            dict: Response containing the latest commit SHA.
        """
        headers = {}
        commits = []

        # Set headers for authorization and content type
        headers["Accept"] = "application/vnd.github+json"

        page = 1
        while True:
            path = f"{self.HOST}/repos/{self.workspace_slug}/{self.repo}/pulls/{self.pr_id}/comments?page={page}&per_page=100"
            response = await self.get(path, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Error fetching commits: {response.status_code}, {response.text}")
            data = response.json()
            if not data:
                break
            commits.extend(data)
            page += 1
        return commits
