from app.backend_common.constants.constants import PRStatus, VCSTypes
from app.backend_common.utils.app_utils import (
    get_gitlab_workspace_slug,
    get_vcs_repo_name_slug,
)
from app.main.blueprints.deputy_dev.models.pr_close_request import PRCloseRequest
from .webhook_utils import should_skip_trayalabs_request


class PullRequestCloseWebhook:
    @classmethod
    async def parse_payload(cls, payload: dict) -> PRCloseRequest:
        """
        Extracts pull request data from the payload based on the VCS type.

        Args:
            payload (Dict[str, Any]): The webhook payload containing PR information.
            vcs_type (str): The type of version control system (e.g., 'bitbucket', 'github').

        Returns:
            Tuple[int, str, str]: A tuple containing PR ID, creation time, and stats_collection time.
        """
        vcs_type = payload.get("vcs_type")
        if should_skip_trayalabs_request(payload):
            return None
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.__parse_bitbucket_payload(payload)
        elif vcs_type == VCSTypes.github.value:
            return cls.__parse_github_payload(payload)
        elif vcs_type == VCSTypes.gitlab.value:
            parsed_payload = cls.__parse_gitlab_payload(payload)
            return parsed_payload
        else:
            raise ValueError("Unsupported VCS type")

    @classmethod
    def __parse_bitbucket_payload(cls, payload: dict) -> PRCloseRequest:
        parsed_payload = {
            "pr_state": payload["pullrequest"]["state"],
            "scm_pr_id": str(payload["pullrequest"]["id"]),
            "repo_name": get_vcs_repo_name_slug(payload["repository"]["full_name"]),
            "workspace": payload["repository"]["workspace"]["slug"],
            "scm_workspace_id": str(payload.get("scm_workspace_id")),
            "workspace_slug": payload["repository"]["workspace"]["slug"],
            "pr_created_at": payload["pullrequest"]["created_on"],
            "pr_closed_at": payload["pullrequest"]["updated_on"],
            "scm_repo_id": payload["repository"]["uuid"],
            "destination_branch": payload["pullrequest"]["destination"]["branch"]["name"],
        }
        return PRCloseRequest(**parsed_payload)

    @classmethod
    def __parse_github_payload(cls, payload: dict) -> PRCloseRequest:
        # TODO - Need to revisit the payload for github, before we start using the payload,
        # define below
        parsed_payload = {
            "pr_state": PRStatus.MERGED.value if payload["pull_request"]["merged"] else PRStatus.DECLINED.value,
            "scm_pr_id": str(payload["pull_request"]["number"]),
            "repo_name": get_vcs_repo_name_slug(payload["pull_request"]["head"]["repo"]["full_name"]),
            "workspace": payload["organization"]["login"],
            "workspace_slug": payload["organization"]["login"],
            "scm_workspace_id": str(payload.get("scm_workspace_id")),
            "pr_created_at": payload["pull_request"]["created_at"],
            "pr_closed_at": payload["pull_request"]["closed_at"],
            "scm_repo_id": str(payload["pull_request"]["head"]["repo"]["id"]),
            "destination_branch": payload["pull_request"]["base"]["ref"],
        }
        return PRCloseRequest(**parsed_payload)

    @classmethod
    def __parse_gitlab_payload(cls, payload: dict) -> PRCloseRequest:
        # TODO - Need to revisit the payload for github, before we start using the payload,
        pr_id = payload["object_attributes"]["iid"]
        workspace = payload["project"]["namespace"]
        workspace_slug = get_gitlab_workspace_slug(payload["project"]["path_with_namespace"])
        parsed_payload = {
            "pr_state": (
                PRStatus.MERGED.value if payload["object_attributes"]["state"] == "merged" else PRStatus.DECLINED.value
            ),
            "scm_pr_id": str(pr_id),
            "repo_name": get_vcs_repo_name_slug(payload["project"]["path_with_namespace"]),
            "scm_repo_id": str(payload["project"]["id"]),
            "workspace": workspace,
            "workspace_slug": workspace_slug,
            "scm_workspace_id": str(payload.get("scm_workspace_id")),
            "pr_created_at": payload["object_attributes"]["created_at"],
            "pr_closed_at": payload["object_attributes"]["updated_at"],
            "destination_branch": payload["object_attributes"]["target_branch"],
        }
        return PRCloseRequest(**parsed_payload)
