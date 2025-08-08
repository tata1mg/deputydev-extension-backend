from typing import Any, Dict, Optional

from app.backend_common.constants.constants import VCSTypes
from app.backend_common.utils.app_utils import (
    get_gitlab_workspace_slug,
    get_vcs_repo_name_slug,
)
from app.main.blueprints.deputy_dev.constants.constants import (
    GithubActions,
    GitlabActions,
)

from .webhook_utils import should_skip_trayalabs_request


class PRWebhook:
    """
    class manages bitbucket webhook
    """

    @classmethod
    async def parse_payload(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        vcs_type = payload.get("vcs_type")
        if should_skip_trayalabs_request(payload):
            return None
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.__parse_bitbucket_payload(payload)
        elif vcs_type == VCSTypes.github.value:
            return cls.__parse_github_payload(payload)
        elif vcs_type == VCSTypes.gitlab.value:
            parsed_payload = await cls.__parse_gitlab_payload(payload)
            return parsed_payload

    @classmethod
    def __parse_bitbucket_payload(cls, bitbucket_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates servable payload from bitbucket payload
        """
        pr_id = bitbucket_payload["pullrequest"]["id"]
        repo_name = get_vcs_repo_name_slug(bitbucket_payload["repository"]["full_name"])
        html_url = bitbucket_payload["repository"]["links"]["html"]["href"]
        repo_origin = html_url.replace("https://", "").lower() + ".git"
        request_id = bitbucket_payload["request_id"]
        workspace = bitbucket_payload["repository"]["workspace"]["name"]
        workspace_slug = bitbucket_payload["repository"]["workspace"]["slug"]
        prompt_version = bitbucket_payload.get("prompt_version", "v2")
        scm_workspace_id = str(bitbucket_payload.get("scm_workspace_id"))
        pr_review_start_time = bitbucket_payload.get("pr_review_start_time")
        vcs_type = VCSTypes.bitbucket.value
        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "repo_origin": repo_origin,
            "request_id": request_id,
            "workspace": workspace,
            "workspace_id": scm_workspace_id,
            "workspace_slug": workspace_slug,
            "vcs_type": vcs_type,
            "prompt_version": prompt_version,
            "pr_review_start_time": pr_review_start_time,
        }

    @classmethod
    def __parse_github_payload(cls, github_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates servable payload from github payload
        """
        #  only gets request for PR open and comment created on a PR with #review tag
        if github_payload.get("action") not in [GithubActions.OPENED.value, GithubActions.CREATED.value]:
            return
        if github_payload.get("issue") and github_payload.get("issue").get("pull_request"):
            return cls.__parse_github_issue_comment_payload(github_payload)

        pr_id = github_payload["pull_request"]["number"]
        repo_name = get_vcs_repo_name_slug(github_payload["pull_request"]["head"]["repo"]["full_name"])
        html_url = github_payload["repository"]["html_url"]
        repo_origin = html_url.replace("https://", "").lower() + ".git"
        request_id = github_payload["request_id"]
        workspace = github_payload["organization"]["login"]
        workspace_slug = github_payload["organization"]["login"]
        prompt_version = github_payload.get("prompt_version", "v2")
        scm_workspace_id = str(github_payload.get("scm_workspace_id"))
        pr_review_start_time = github_payload.get("pr_review_start_time")
        vcs_type = VCSTypes.github.value
        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "repo_origin": repo_origin,
            "request_id": request_id,
            "workspace": workspace,
            "workspace_id": scm_workspace_id,
            "workspace_slug": workspace_slug,
            "vcs_type": vcs_type,
            "prompt_version": prompt_version,
            "pr_review_start_time": pr_review_start_time,
        }

    @classmethod
    def __parse_github_issue_comment_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GitHub issue comment payload for PR conversation comments
        Only handles comments created on PR conversation
        """
        # Check if it's a comment on PR and it's a created action
        if not (payload.get("issue", {}).get("pull_request") and payload.get("action") == GithubActions.CREATED.value):
            return None

        # Extract PR number from pull_request URL
        pr_url = payload["issue"]["pull_request"]["url"]
        pr_id = pr_url.split("/")[-1]
        pr_review_start_time = payload.get("pr_review_start_time")
        html_url = payload["repository"]["html_url"]
        repo_origin = html_url.replace("https://", "").lower() + ".git"

        return {
            "pr_id": int(pr_id),
            "repo_name": get_vcs_repo_name_slug(payload["repository"]["full_name"]),
            "repo_origin": repo_origin,
            "request_id": payload["request_id"],
            "workspace": payload["organization"]["login"],
            "workspace_id": str(payload.get("scm_workspace_id")),
            "workspace_slug": payload["organization"]["login"],
            "vcs_type": VCSTypes.github.value,
            "prompt_version": payload.get("prompt_version", "v2"),
            "pr_review_start_time": pr_review_start_time,
        }

    @classmethod
    async def __parse_gitlab_payload(cls, gitlab_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generates servable payload from gitlab merge request (MR) payload
        """
        if (
            gitlab_payload.get("object_kind") == "merge_request"
            and gitlab_payload.get("object_attributes", {}).get("state") != GitlabActions.OPENED.value
        ):
            return None
        pr_id = gitlab_payload["object_attributes"]["iid"]
        repo_name = get_vcs_repo_name_slug(gitlab_payload["project"]["path_with_namespace"])
        html_url = gitlab_payload["project"]["web_url"]
        repo_origin = html_url.replace("https://", "").lower() + ".git"
        request_id = gitlab_payload["request_id"]
        workspace = gitlab_payload["project"]["namespace"]
        workspace_slug = get_gitlab_workspace_slug(gitlab_payload["project"]["path_with_namespace"])
        repo_id = gitlab_payload["project"]["id"]
        prompt_version = gitlab_payload.get("prompt_version", "v2")
        scm_workspace_id = str(gitlab_payload.get("scm_workspace_id"))
        pr_review_start_time = gitlab_payload.get("pr_review_start_time")
        vcs_type = VCSTypes.gitlab.value

        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "repo_origin": repo_origin,
            "request_id": str(request_id),
            "workspace": workspace,
            "workspace_id": scm_workspace_id,
            "repo_id": str(repo_id),
            "workspace_slug": workspace_slug,
            "vcs_type": vcs_type,
            "prompt_version": prompt_version,
            "pr_review_start_time": pr_review_start_time,
        }
