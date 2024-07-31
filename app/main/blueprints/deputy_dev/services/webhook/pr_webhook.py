from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.common.utils.app_utils import get_last_part


class PRWebhook:
    """
    class manages bitbucket webhook
    """

    @classmethod
    def parse_payload(cls, payload, vcs_type):
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.__parse_bitbucket_payload(payload)
        elif vcs_type == VCSTypes.github.value:
            return cls.__parse_github_payload(payload)

    @classmethod
    def __parse_bitbucket_payload(cls, bitbucket_payload):
        """
        Generates servable payload from bitbucket payload
        """
        pr_id = bitbucket_payload["pullrequest"]["id"]
        repo_name = get_last_part(bitbucket_payload["repository"]["full_name"])
        request_id = bitbucket_payload["request_id"]
        workspace = bitbucket_payload["repository"]["workspace"]["slug"]
        workspace_id = bitbucket_payload["repository"]["workspace"]["uuid"]
        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "request_id": request_id,
            "workspace": workspace,
            "workspace_id": workspace_id,
        }

    @classmethod
    def __parse_github_payload(cls, github_payload):
        """
        Generates servable payload from github payload
        """
        pr_id = github_payload["pull_request"]["number"]
        repo_name = github_payload["pull_request"]["head"]["repo"]["name"]
        request_id = github_payload["request_id"]
        workspace = github_payload["organization"]["login"]
        workspace_id = str(github_payload["organization"]["id"])
        return {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "request_id": request_id,
            "workspace": workspace,
            "workspace_id": workspace_id,
        }
