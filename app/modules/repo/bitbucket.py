from datetime import datetime
from typing import Any, Dict

import requests
import re
from sanic.log import logger
from torpedo import CONFIG

from app.dao.repo import PullRequestResponse
from app.utils import ignore_files
from app.constants.jira import ATLASSIAN_ISSUE_URL_PREFIX, ISSUE_ID_REGEX


class BitBucketModule:
    """
    A class for interacting with Bitbucket API.
    """

    def __init__(self, workspace: str, pr_id: int) -> None:
        self.workspace = workspace
        self.pr_id = pr_id
        self.bitbucket_url = CONFIG.config["BITBUCKET"]["URL"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": CONFIG.config["BITBUCKET"]["KEY"],
        }

    async def get_pr_details(self) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket.

        Returns:
            PullRequestResponse: An object containing details of the pull request.

        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        diff_url = f"{self.bitbucket_url}/{self.workspace}/pullrequests/{self.pr_id}"
        response = requests.get(
            diff_url,
            headers=self.headers,
        )
        if response.status_code != 200:
            response = f"Unable to process PR - {self.pr_id}: {response._content}"
            logger.error(response)
            raise ValueError(response)
        else:
            data = response.json()
            data['issue_id'] = self.get_issue_id(data.get('rendered', {}).get('title', {}))
            data["created_on"] = datetime.fromisoformat(data["created_on"])
            data["updated_on"] = datetime.fromisoformat(data["updated_on"])
            return PullRequestResponse(**data)

    def get_issue_id(self, title) -> str:
        title_html = title.get('html', '')
        escaped_prefix = re.escape(ATLASSIAN_ISSUE_URL_PREFIX) + ISSUE_ID_REGEX
        matched_text = re.search(escaped_prefix, title_html)
        if matched_text is not None:
           issue_url = matched_text.group()
           return issue_url.replace(ATLASSIAN_ISSUE_URL_PREFIX, '')

    async def get_pr_diff(self) -> str:
        """
        Get the diff of a pull request from Bitbucket.

        Returns:
            str: The diff of the pull request.

        Raises:
            ValueError: If the diff cannot be retrieved.
        """
        diff_url = f"{self.bitbucket_url}/{self.workspace}/pullrequests/{self.pr_id}/diff"
        response = requests.get(
            diff_url,
            headers=self.headers,
        )
        if response.status_code != 200:
            response = f"Unable to retrieve diff for PR - {self.pr_id}: {response._content}"
            logger.error(response)
            raise ValueError(response)
        else:
            return ignore_files(response)

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
            "Authorization": CONFIG.config[model]["BITBUCKET_TOKEN"],
        }
        url = f"{self.bitbucket_url}/{self.workspace}/pullrequests/{self.pr_id}/comments"
        response = requests.post(url, headers=comment_headers, json=comment)
        return response.json()
