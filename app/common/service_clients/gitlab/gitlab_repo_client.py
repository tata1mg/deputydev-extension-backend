import requests
from sanic.log import logger

from app.common.service_clients.base_scm_client import BaseSCMClient
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler


class GitlabRepoClient(BaseSCMClient):
    """
    A class for interacting with Bitbucket API.
    """

    def __init__(self, pr_id: str, project_id: str, auth_handler: AuthHandler) -> None:
        super().__init__(auth_handler=auth_handler)
        self.pr_id = pr_id
        self.gitlab_url = "https://gitlab.com/api/v4"
        self.project_id = project_id

    async def get_namespace_id(self, workspace_slug):
        query_params = {"search": workspace_slug}
        path = f"{self.gitlab_url}/namespaces"
        response = requests.get(path, params=query_params)
        return response.json()[0]["id"]

    async def create_pr_comment(self, comment_payload: dict):
        """
        Creates a comment on the entire merge request.

        Parameters:
        - project_id (str): The project ID in GitLab (equivalent to repo_id).
        - merge_request_iid (str): The merge request IID (internal ID).
        - comment_payload (dict): The payload of the comment (e.g., body).

        Returns:
        - dict: Response data from the API or error message.
        """
        path = f"{self.gitlab_url}/projects/{self.project_id}/merge_requests/{self.pr_id}/notes"
        workspace_token_headers = await self.get_ws_token_headers()
        response = await self.post(path, json=comment_payload, headers=workspace_token_headers, skip_headers=True)
        return response

    async def create_pr_review_comment(self, comment_payload: dict):
        """
        Creates a comment on the entire merge request.

        Parameters:
        - project_id (str): The project ID in GitLab (equivalent to repo_id).
        - merge_request_iid (str): The merge request IID (internal ID).
        - comment_payload (dict): The payload of the comment (e.g., body).

        Returns:
        - dict: Response data from the API or error message.
        """
        path = f"{self.gitlab_url}/projects/{self.project_id}/merge_requests/{self.pr_id}/discussions"
        workspace_token_headers = await self.get_ws_token_headers()
        response = await self.post(path, json=comment_payload, headers=workspace_token_headers, skip_headers=True)
        return response

    async def get_pr_details(self) -> dict:
        """
        Get details of a pull request from Bitbucket.

        Returns:
            dict: pre details response
        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        url = f"{self.gitlab_url}/projects/{self.project_id}/merge_requests/{self.pr_id}"
        response = await self.get(url)
        if response.status_code != 200:
            logger.error(f"Unable to process PR - {self.pr_id}: {response.content}")
            return
        return response.json()

    async def update_pr_details(self, payload) -> dict:
        """
        Update details of a pull request from Bitbucket.

        Returns:
            dict: pre details response
        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        url = f"{self.gitlab_url}/projects/{self.project_id}/merge_requests/{self.pr_id}"
        workspace_token_headers = await self.get_ws_token_headers()
        response = await self.put(url, json=payload, headers=workspace_token_headers, skip_headers=True)
        return response.json()

    async def get_pr_diff(self):
        """
        Get the diff of a pull request from Bitbucket.

        Returns:
            str: The diff of the pull request.
        """
        diff_url = f"{self.gitlab_url}/projects/{self.project_id}/merge_requests/{self.pr_id}/changes"
        response = await self.get(diff_url)
        if response.status_code != 200:
            logger.error(f"Unable to retrieve diff for PR - {self.pr_id}: {response._content}")
        return response.json(), response.status_code

    async def get_discussion_comments(self, discussion_id):
        diff_url = f"{self.gitlab_url}/projects/{self.project_id}/merge_requests/{self.pr_id}/discussions/{discussion_id}/notes"
        response = await self.get(diff_url)
        if response.status_code != 200:
            logger.error(f"Unable to retrieve discussoin thread comments- {self.pr_id}: {response._content}")
        return response.json()

    async def create_discussion_comment(self, comment_payload, discussion_id):
        workspace_token_headers = await self.get_ws_token_headers()
        diff_url = f"{self.gitlab_url}/projects/{self.project_id}/merge_requests/{self.pr_id}/discussions/{discussion_id}/notes"
        response = await self.post(diff_url, json=comment_payload, headers=workspace_token_headers, skip_headers=True)
        if response.status_code != 200:
            logger.error(f"Unable to retrieve discussoin thread comments- {self.pr_id}: {response._content}")
        return response.json()
