from app.common.service_clients.gitlab.gitlab_repo_client import GitlabRepoClient
from app.common.utils.app_utils import get_gitlab_workspace_slug, get_vcs_repo_name_slug
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.models.human_comment_request import (
    HumanCommentRequest,
)


class HumanCommentWebhook:
    """
    class manages bitbucket webhook
    """

    @classmethod
    async def parse_payload(cls, payload, vcs_type):
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.__parse_bitbucket_payload(payload)
        elif vcs_type == VCSTypes.github.value:
            return cls.__parse_github_payload(payload)
        elif vcs_type == VCSTypes.gitlab.value:
            parsed_payload = await cls.__parse_gitlab_payload(payload)
            return parsed_payload

    @classmethod
    def __parse_bitbucket_payload(cls, payload):
        """
        Generates servable payload from bitbucket payload
        """
        parsed_payload = {
            "scm_workspace_id": payload["repository"]["workspace"]["uuid"],
            "repo_name": get_vcs_repo_name_slug(payload["repository"]["full_name"]),
            "scm_repo_id": payload["repository"]["uuid"],
            "actor": payload["actor"]["display_name"],
            "scm_pr_id": str(payload["pullrequest"]["id"]),
        }
        return HumanCommentRequest(**parsed_payload)

    @classmethod
    def __parse_github_payload(cls, payload):
        """
        Generates servable payload from github payload
        """
        parsed_payload = {
            "scm_workspace_id": str(payload["organization"]["id"]),
            "repo_name": get_vcs_repo_name_slug(payload["pull_request"]["head"]["repo"]["full_name"]),
            "scm_repo_id": str(payload["pull_request"]["head"]["repo"]["id"]),
            "actor": payload["comment"]["user"]["login"],
            "scm_pr_id": str(payload["pull_request"]["number"]),
        }
        return HumanCommentRequest(**parsed_payload)

    @classmethod
    async def __parse_gitlab_payload(cls, payload):
        """
        Generates servable payload from github payload
        """
        pr_id = payload["merge_request"]["iid"]
        workspace = payload["project"]["namespace"]
        slug = get_gitlab_workspace_slug(payload["project"]["path_with_namespace"])
        workspace_id = await GitlabRepoClient(pr_id=pr_id, project_id=workspace).get_namespace_id(slug)
        parsed_payload = {
            "scm_workspace_id": str(workspace_id),
            "repo_name": get_vcs_repo_name_slug(payload["project"]["path_with_namespace"]),
            "scm_repo_id": str(payload["project"]["id"]),
            "actor": payload["user"]["username"],
            "scm_pr_id": str(payload["merge_request"]["iid"]),
        }
        return HumanCommentRequest(**parsed_payload)
