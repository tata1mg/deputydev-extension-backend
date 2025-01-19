from app.backend_common.utils.app_utils import (
    get_gitlab_workspace_slug,
    get_vcs_repo_name_slug,
)
from app.common.constants.constants import VCSTypes
from app.main.blueprints.deputy_dev.constants.constants import (
    GithubActions,
    GitlabActions,
)


class PRWebhook:
    """
    class manages bitbucket webhook
    """

    @classmethod
    async def parse_payload(cls, payload):
        vcs_type = payload.get("vcs_type")
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.__parse_bitbucket_payload(payload)
        elif vcs_type == VCSTypes.github.value:
            return cls.__parse_github_payload(payload)
        elif vcs_type == VCSTypes.gitlab.value:
            parsed_payload = await cls.__parse_gitlab_payload(payload)
            return parsed_payload

    @classmethod
    def __parse_bitbucket_payload(cls, bitbucket_payload):
        """
        Generates servable payload from bitbucket payload
        """
        pr_id = bitbucket_payload["pullrequest"]["id"]
        repo_name = get_vcs_repo_name_slug(bitbucket_payload["repository"]["full_name"])
        request_id = bitbucket_payload["request_id"]
        workspace = bitbucket_payload["repository"]["workspace"]["name"]
        workspace_slug = bitbucket_payload["repository"]["workspace"]["slug"]
        prompt_version = bitbucket_payload.get("prompt_version", "v2")
        scm_workspace_id = str(bitbucket_payload.get("scm_workspace_id"))
        vcs_type = VCSTypes.bitbucket.value
        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "request_id": request_id,
            "workspace": workspace,
            "workspace_id": scm_workspace_id,
            "workspace_slug": workspace_slug,
            "vcs_type": vcs_type,
            "prompt_version": prompt_version,
        }

    @classmethod
    def __parse_github_payload(cls, github_payload):
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
        request_id = github_payload["request_id"]
        workspace = github_payload["organization"]["login"]
        workspace_slug = github_payload["organization"]["login"]
        prompt_version = github_payload.get("prompt_version", "v2")
        scm_workspace_id = str(github_payload.get("scm_workspace_id"))
        vcs_type = VCSTypes.github.value
        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "request_id": request_id,
            "workspace": workspace,
            "workspace_id": scm_workspace_id,
            "workspace_slug": workspace_slug,
            "vcs_type": vcs_type,
            "prompt_version": prompt_version,
        }

    @classmethod
    def __parse_github_issue_comment_payload(cls, payload):
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

        return {
            "pr_id": int(pr_id),
            "repo_name": get_vcs_repo_name_slug(payload["repository"]["full_name"]),
            "request_id": payload["request_id"],
            "workspace": payload["organization"]["login"],
            "workspace_id": str(payload.get("scm_workspace_id")),
            "workspace_slug": payload["organization"]["login"],
            "vcs_type": VCSTypes.github.value,
            "prompt_version": payload.get("prompt_version", "v2"),
        }

    @classmethod
    async def __parse_gitlab_payload(cls, gitlab_payload):
        """
        Generates servable payload from gitlab merge request (MR) payload
        """
        if (
            gitlab_payload.get("object_kind") == "merge_request"
            and gitlab_payload.get("object_attributes", {}).get("state") != GitlabActions.OPENED.value
        ):
            return
        pr_id = gitlab_payload["object_attributes"]["iid"]
        repo_name = get_vcs_repo_name_slug(gitlab_payload["project"]["path_with_namespace"])
        request_id = gitlab_payload["request_id"]
        workspace = gitlab_payload["project"]["namespace"]
        workspace_slug = get_gitlab_workspace_slug(gitlab_payload["project"]["path_with_namespace"])
        repo_id = gitlab_payload["project"]["id"]
        prompt_version = gitlab_payload.get("prompt_version", "v2")
        scm_workspace_id = str(gitlab_payload.get("scm_workspace_id"))
        vcs_type = VCSTypes.gitlab.value

        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "request_id": str(request_id),
            "workspace": workspace,
            "workspace_id": scm_workspace_id,
            "repo_id": str(repo_id),
            "workspace_slug": workspace_slug,
            "vcs_type": vcs_type,
            "prompt_version": prompt_version,
        }
