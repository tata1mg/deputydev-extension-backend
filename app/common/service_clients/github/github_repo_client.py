import requests
from sanic.log import logger
from torpedo import CONFIG

config = CONFIG.config


class GithubRepoClient:
    """
    class handles rest api calls for Github PR reviews
    """

    BEARER_TOKEN = config["GITHUB"]["BEARER_TOKEN"]
    HOST = config["GITHUB"]["HOST"]

    @classmethod
    def auth_token(cls):
        return cls.BEARER_TOKEN

    @classmethod
    async def create_pr_comment(cls, user_name: str, repo_name: str, pr_id: int, payload: dict, headers=None):
        """
        creates comment on whole PR
        """
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {cls.auth_token()}"
        path = f"{cls.HOST}/repos/{user_name}/{repo_name}/issues/{pr_id}/comments"
        try:
            result = requests.post(path, json=payload, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to comment on github pr for repo_name: {repo_name}, "
                f"pr_id: {pr_id}, user_name: {user_name} err {ex}"
            )

    @classmethod
    async def update_pr(cls, user_name: str, repo_name: str, pr_id: int, payload: dict, headers: dict = None):
        """
        Updates PR properties like description
        """
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {cls.auth_token()}"
        path = f"{cls.HOST}/repos/{user_name}/{repo_name}/issues/{pr_id}"
        try:
            result = requests.patch(path, json=payload, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to  update pr for repo_name: {repo_name}, " f"pr_id: {pr_id}, user_name: {user_name} err {ex}"
            )

    @classmethod
    async def create_pr_review_comment(
        cls, user_name: str, repo_name: str, pr_id: str, payload: dict, headers: dict = None
    ):
        """
        Creates pr review comment on a file and line
        """
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {cls.auth_token()}"
        path = f"{cls.HOST}/repos/{user_name}/{repo_name}/pulls/{pr_id}/comments"
        try:
            result = requests.post(path, json=payload, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to comment on github pr for repo_name: {repo_name}, "
                f"pr_id: {pr_id}, user_name: {user_name} err {ex}"
            )

    @classmethod
    async def get_pr_diff(cls, user_name, repo_name, pr_id, headers=None):
        """
        returns pr diff in git format
        """
        headers = headers or {}
        path = f"{cls.HOST}/repos/{user_name}/{repo_name}/pulls/{pr_id}"
        headers["Accept"] = "application/vnd.github.v3.diff"
        headers["Authorization"] = f"Bearer {cls.auth_token()}"
        try:
            result = requests.get(path, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to get github pr diff for repo_name: {repo_name}, "
                f"pr_id: {pr_id}, user_name: {user_name} err {ex}"
            )

    @classmethod
    async def get_pr_details(cls, user_name, repo_name, pr_id, headers=None):
        """
        returns pr details
        """
        headers = headers or {}
        path = f"{cls.HOST}/repos/{user_name}/{repo_name}/pulls/{pr_id}"
        headers["Authorization"] = f"Bearer {cls.auth_token()}"
        headers["Accept"] = "application/vnd.github+json"
        try:
            result = requests.get(path, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to get github pr details for repo_name: {repo_name}, "
                f"pr_id: {pr_id}, user_name: {user_name} er {ex}"
            )

    @classmethod
    async def get_comment_thread(cls, user_name, repo_name, comment_id, headers=None):
        """
        returns comment thread
        """
        headers = headers or {}
        path = f"{cls.HOST}/repos/{user_name}/{repo_name}/pulls/comments/{comment_id}"
        headers["Authorization"] = f"Bearer {cls.auth_token()}"
        headers["Accept"] = "application/vnd.github+json"
        try:
            result = requests.get(path, headers=headers)
            return result
        except Exception as ex:
            logger.error(
                f"unable to get github comment thread details for repo_name: {repo_name}, "
                f"comment_id: {comment_id}, user_name: {user_name} er {ex}"
            )
