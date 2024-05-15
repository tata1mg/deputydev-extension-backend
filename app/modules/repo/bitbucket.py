from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import requests
from torpedo import CONFIG

from app.modules.repo.schemas import PullRequestResponse
from app.utils import ignore_files


@dataclass
class BitBucketModule:
    """
    A class for interacting with Bitbucket API.
    """

    workspace: str
    pr_id: int
    bitbucket_url = CONFIG.config["BITBUCKET"]["URL"]
    headers = {
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
            raise ValueError("Unable to process the PR")
        else:
            data = response.json()
            created_time = datetime.fromisoformat(data["created_on"][:-6])
            updated_time = datetime.fromisoformat(data["updated_on"][:-6])

            # Calculate the time difference in minutes
            time_difference = (updated_time - created_time).total_seconds() / 60
            if time_difference > 5:
                return PullRequestResponse(created=False, **data)
            else:
                return PullRequestResponse(created=True, **data)

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
            raise ValueError("Unable to retrieve PR diff.")
        else:
            return ignore_files(response)

    async def create_comment_on_pr(self, comment: str) -> Dict[str, Any]:
        """
        Create a comment on the pull request.

        Parameters:
        - comment (str): The content of the comment.

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        url = f"{self.bitbucket_url}/{self.workspace}/pullrequests/{self.pr_id}/comments"
        comment_payload = {"content": {"raw": comment}}
        response = requests.post(url, headers=self.headers, json=comment_payload)
        return response.json()
