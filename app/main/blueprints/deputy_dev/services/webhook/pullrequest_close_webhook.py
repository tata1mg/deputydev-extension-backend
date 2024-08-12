from app.common.utils.app_utils import convert_to_datetime, get_bitbucket_repo_name_slug
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes


class PullRequestCloseWebhook:
    @classmethod
    def parse_payload(cls, payload: dict, vcs_type: str) -> dict:
        """
        Extracts pull request data from the payload based on the VCS type.

        Args:
            payload (Dict[str, Any]): The webhook payload containing PR information.
            vcs_type (str): The type of version control system (e.g., 'bitbucket', 'github').

        Returns:
            Tuple[int, str, str]: A tuple containing PR ID, creation time, and stats_collection time.
        """
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.__parse_bitbucket_payload(payload)
        # elif vcs_type == VCSTypes.github.value: #TODO Integrate for github later
        #     return cls.__parse_github_payload(payload)
        else:
            raise ValueError("Unsupported VCS type")

    @classmethod
    def __parse_bitbucket_payload(cls, payload: dict) -> dict:
        payload = {
            "pr_state": payload["pullrequest"]["state"],
            "pr_id": payload["pullrequest"]["id"],
            "repo_name": get_bitbucket_repo_name_slug(payload["repository"]["full_name"]),
            "workspace": payload["repository"]["workspace"]["slug"],
            "workspace_id": payload["repository"]["workspace"]["uuid"],
            "pr_created_at": convert_to_datetime(payload["pullrequest"]["created_on"]),
            "pr_closed_at": convert_to_datetime(payload["pullrequest"]["updated_on"]),
        }
        return payload

    @classmethod
    def __parse_github_payload(cls, payload: dict) -> dict:
        # TODO - Need to revisit the payload for github, before we start using the payload,
        # define below
        payload = {
            "pr_id": payload["pull_request"]["id"],
            "repo_name": payload["repository"]["name"],
            "workspace": payload["organization"]["login"],
            "workspace_id": str(payload["organization"]["id"]),
            "pr_created_at": convert_to_datetime(payload["pull_request"]["created_at"]),
            "pr_closed_at": convert_to_datetime(payload["pull_request"]["merged_at"]),
        }
        return payload
