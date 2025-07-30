from typing import Optional

from app.backend_common.constants.constants import VCSTypes
from app.backend_common.utils.app_utils import get_vcs_repo_name_slug
from app.main.blueprints.deputy_dev.models.issue_comment_request import (
    IssueCommentRequest,
)
from app.main.blueprints.deputy_dev.utils import remove_special_char
from .webhook_utils import should_skip_trayalabs_request


class IssueCommentWebhook:
    @classmethod
    async def parse_payload(cls, request_payload) -> Optional[IssueCommentRequest]:
        """Parse issue comment webhook payload"""
        if should_skip_trayalabs_request(request_payload):
            return None
        if request_payload.get("vcs_type") == VCSTypes.bitbucket.value:
            return cls.__parse_bitbucket_issue_payload(request_payload)
        # Add support for other VCS types here
        return None

    @classmethod
    def __parse_bitbucket_issue_payload(cls, request_payload) -> IssueCommentRequest:
        """
        Parse Bitbucket issue comment payload
        Returns structured data containing comment, repo, and issue information
        """
        parsed_payload = {
            "issue_id": str(request_payload["issue"]["id"]),
            "issue_description": request_payload["issue"]["content"]["raw"],
            "issue_title": request_payload["issue"]["title"],
            "issue_comment": remove_special_char("\\", request_payload["comment"]["content"]["raw"]),
            "repo_name": get_vcs_repo_name_slug(request_payload["repository"]["full_name"]),
            "workspace": request_payload["repository"]["workspace"]["name"],
            "workspace_slug": request_payload["repository"]["workspace"]["slug"],
            "scm_workspace_id": str(request_payload.get("scm_workspace_id")),
            "vcs_type": VCSTypes.bitbucket.value,
        }
        return IssueCommentRequest(**parsed_payload)
