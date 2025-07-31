from app.backend_common.constants.constants import VCSTypes
from app.backend_common.utils.app_utils import (
    get_gitlab_workspace_slug,
    get_vcs_repo_name_slug,
)
from app.main.blueprints.deputy_dev.models.pr_approval_request import PRApprovalRequest
from .webhook_utils import should_skip_trayalabs_request


class PRApprovalWebhook:
    """
    class manages bitbucket webhook
    """

    @classmethod
    async def parse_payload(cls, payload):
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
    def __parse_bitbucket_payload(cls, payload):
        """
        Generates servable payload from bitbucket payload
        """
        parsed_payload = {
            "scm_workspace_id": str(payload.get("scm_workspace_id")),
            "repo_name": get_vcs_repo_name_slug(payload["repository"]["full_name"]),
            "scm_repo_id": payload["repository"]["uuid"],
            "actor": payload["actor"]["display_name"],
            "scm_pr_id": str(payload["pullrequest"]["id"]),
            "scm_approval_time": payload["approval"]["date"],
            "pr_created_at": payload["pullrequest"]["created_on"],
            "workspace": payload["repository"]["workspace"]["slug"],
            "workspace_slug": payload["repository"]["workspace"]["slug"],
        }
        return PRApprovalRequest(**parsed_payload)

    @classmethod
    def __parse_github_payload(cls, payload):
        """
        Generates servable payload from github payload
        """
        parsed_payload = {
            "scm_workspace_id": str(payload.get("scm_workspace_id")),
            "repo_name": get_vcs_repo_name_slug(payload["pull_request"]["head"]["repo"]["full_name"]),
            "scm_repo_id": str(payload["pull_request"]["head"]["repo"]["id"]),
            "actor": payload["review"]["user"]["login"],
            "scm_pr_id": str(payload["pull_request"]["number"]),
            "scm_approval_time": payload["review"]["submitted_at"],
            "pr_created_at": payload["pull_request"]["created_at"],
            "workspace": payload["organization"]["login"],
            "workspace_slug": payload["organization"]["login"],
        }
        return PRApprovalRequest(**parsed_payload)

    @classmethod
    async def __parse_gitlab_payload(cls, payload):
        """
        Generates servable payload from github payload
        """
        parsed_payload = {
            "scm_workspace_id": str(payload.get("scm_workspace_id")),
            "repo_name": get_vcs_repo_name_slug(payload["project"]["path_with_namespace"]),
            "scm_repo_id": str(payload["project"]["id"]),
            "actor": payload["user"]["username"],
            "scm_pr_id": str(payload["object_attributes"]["iid"]),
            "scm_approval_time": payload["object_attributes"]["updated_at"],
            "pr_created_at": payload["object_attributes"]["created_at"],
            "workspace": payload["project"]["namespace"],
            "workspace_slug": get_gitlab_workspace_slug(payload["project"]["path_with_namespace"]),
        }
        return PRApprovalRequest(**parsed_payload)
