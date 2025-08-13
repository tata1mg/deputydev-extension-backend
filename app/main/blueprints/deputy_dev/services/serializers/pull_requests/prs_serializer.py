from typing import Any, Dict, List

from app.main.blueprints.deputy_dev.constants.constants import SCMType
from app.main.blueprints.deputy_dev.constants.serializers_constants import (
    CommentDeeplinks,
)


class PrsSerializer:
    """
    Serializer for processing pull request data.

    Attributes:
        raw_data (List[Dict[str, Any]]): The raw pull request data to be processed.
    """

    def __init__(self, raw_data: List[Dict[str, Any]]) -> None:
        self.raw_data = raw_data

    def process_raw_data(self) -> List[Dict[str, Any]]:
        """
        Processes the raw pull request data into a structured format.

        Returns:
            List[Dict[str, Any]]: A list of processed pull request objects.
        """
        processed_prs = []

        for item in self.raw_data:
            # Format deep link URL
            if item["scm"] == SCMType.BITBUCKET.value:
                deep_link = CommentDeeplinks.BITBUCKET.value.format(
                    workspace=item["workspace_name"],
                    repo=item["repo_name"],
                    pr_id=item["scm_pr_id"],
                    comment_id=item["scm_comment_id"],
                )
            elif item["scm"] == SCMType.GITHUB.value:
                deep_link = CommentDeeplinks.GITHUB.value.format(
                    workspace=item["workspace_name"],
                    repo=item["repo_name"],
                    pr_id=item["scm_pr_id"],
                    comment_id=item["scm_comment_id"],
                )

            # Create processed PR object
            processed_pr = {
                "repo_name": item["repo_name"],
                "scm_pr_id": item["scm_pr_id"],
                "pr_title": item["pr_title"],
                "scm_comment_id": item["scm_comment_id"],
                "deep_link": deep_link,
            }

            processed_prs.append(processed_pr)

        return processed_prs
