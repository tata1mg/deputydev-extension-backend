from typing import Any, Dict

import requests
from sanic.log import logger
from torpedo import CONFIG


class BitbucketRepoClient:
    """
    A class for interacting with Bitbucket API.
    """

    def __init__(self, workspace: str, repo: str, pr_id: int) -> None:
        self.workspace = workspace
        self.pr_id = pr_id
        self.repo = repo
        self.bitbucket_url = CONFIG.config["BITBUCKET"]["URL"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": CONFIG.config["BITBUCKET"]["KEY"],
        }

    async def get_pr_details(self) -> dict:
        """
        Get details of a pull request from Bitbucket.

        Returns:
            dict: pre details response
        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        diff_url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace}/{self.repo}/pullrequests/{self.pr_id}"
        response = requests.get(
            diff_url,
            headers=self.headers,
        )
        if response.status_code != 200:
            logger.error(f"Unable to process PR - {self.pr_id}: {response._content}")
            return
        return response.json()

    async def get_pr_comments(self) -> list:
        """
        Get all comments for the pull request, handling pagination.

        Returns:
            list: List of all comments for the pull request.
        """
        comments = []
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace}/{self.repo}/pullrequests/{self.pr_id}/comments"

        while url:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            comments.extend(data.get("values", []))
            url = data.get("next")

        return comments

    async def get_pr_diff(self):
        """
        Get the diff of a pull request from Bitbucket.

        Returns:
            str: The diff of the pull request.
        """
        diff_url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace}/{self.repo}/pullrequests/{self.pr_id}/diff"
        response = requests.get(
            diff_url,
            headers=self.headers,
        )
        if response.status_code != 200:
            logger.error(f"Unable to retrieve diff for PR - {self.pr_id}: {response._content}")
        return response, response.status_code

    async def create_comment_on_pr(self, comment: dict, model: str) -> Dict[str, Any]:
        """
        Create a comment on the pull request.

        Parameters:
        - comment (str): The content of the comment.
        - model(str): model which was used to receive comment. Helps identify the bot to post comment

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment_headers = {
            "Content-Type": "application/json",
            "Authorization": CONFIG.config["LLM_MODELS"][model]["BITBUCKET_TOKEN"],
        }
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace}/{self.repo}/pullrequests/{self.pr_id}/comments"
        response = requests.post(url, headers=comment_headers, json=comment)
        return response.json()

    async def get_comment_details(self, comment_id):
        """
        Get the comment details on PR from Bitbucket.

        Returns:
            Dict: Comment Details

        Raises:
            ValueError: If the diff cannot be retrieved.
        """
        url = f"{self.bitbucket_url}/2.0/repositories/{self.workspace}/{self.repo}/pullrequests/{self.pr_id}/comments/{comment_id}"
        response = requests.get(
            url,
            headers=self.headers,
        )
        if response.status_code != 200:
            logger.error(
                f"Unable to retrieve Comment details for comment: {comment_id} - PR ID: {self.pr_id}: {response._content}"
            )
        return response

    async def get_pr_diff_stats(self):
        """
        Get the diff stat of pull request

        Returns:
            str: The diff of the pull request.
        """
        diff_url = (
            f"{self.bitbucket_url}/2.0/repositories/{self.workspace}/{self.repo}/pullrequests/{self.pr_id}/diffstat"
        )
        response = requests.get(
            diff_url,
            headers=self.headers,
        )
        if response.status_code != 200:
            logger.error(
                f"Unable to retrieve diff for PR - {self.pr_id} workspace " f"{self.workspace}: {response._content}"
            )
            return None
        return response

    async def fetch_diffstat(self, repo_name, scm_pr_id):
        url = "https://api.bitbucket.org/2.0/repositories/tata1mg/{repo_name}/pullrequests/{scm_pr_id}/diffstat".format(
            repo_name=repo_name, scm_pr_id=scm_pr_id
        )
        response = requests.get(
            url,
            headers=self.headers,
        )
        if response.status_code == 200:
            data = response.json()
            return sum(file["lines_added"] + file["lines_removed"] for file in data["values"])
        else:
            return 0

    async def get_pr_diff_v1(self, repo_name, scm_pr_id):
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
        response = requests.get(
            diff_url,
            headers=self.headers,
        )
        if response.status_code != 200:
            logger.error(f"Unable to retrieve diff for PR - {self.pr_id}: {response._content}")
        return response, response.status_code
