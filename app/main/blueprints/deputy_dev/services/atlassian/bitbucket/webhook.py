class WebhookManager:
    """
    class manages bitbucket webhook
    """

    @classmethod
    def parse_deputy_dev_payload(cls, bitbucket_payload):
        """
        Generates servable payload from bitbucket payload
        """
        pr_id = bitbucket_payload["pullrequest"]["id"]
        repo_name = bitbucket_payload["pullrequest"]["source"]["repository"]["full_name"]
        request_id = bitbucket_payload["request_id"]
        return {"pr_id": pr_id, "repo_name": repo_name, "request_id": request_id}
