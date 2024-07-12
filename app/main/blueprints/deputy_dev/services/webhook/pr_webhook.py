from app.main.blueprints.deputy_dev.constants.repo import VCSTypes


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
        repo_name = bitbucket_payload["repository"]["name"]
        request_id = bitbucket_payload["request_id"]
        workspace = bitbucket_payload["repository"]["workspace"]["slug"]
        return {"pr_id": pr_id, "repo_name": repo_name, "request_id": request_id, "workspace": workspace}

    @classmethod
    def __parse_github_payload(cls, github_payload):
        """
        Generates servable payload from github payload
        """
        pr_id = github_payload["pull_request"]["id"]
        repo_name = github_payload["pull_request"]["head"]["repo"]["name"]
        request_id = github_payload["request_id"]
        workspace = github_payload["pull_request"]["head"]["repo"]["owner"]["login"]
        return {"pr_id": pr_id, "repo_name": repo_name, "request_id": request_id, "workspace": workspace}
