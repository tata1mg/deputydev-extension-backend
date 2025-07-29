from sanic.log import logger

from app.backend_common.constants.constants import VCSTypes
from app.backend_common.utils.app_utils import (
    get_gitlab_workspace_slug,
    get_vcs_repo_name_slug,
)
from app.main.blueprints.deputy_dev.constants.constants import GithubActions
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import remove_special_char
from deputydev_core.utils.context_vars import set_context_values


class ChatWebhook:
    """
    class manages bitbucket webhook
    """

    @classmethod
    def get_raw_comment(cls, payload):
        vcs_type = payload.get("vcs_type")
        if vcs_type == VCSTypes.bitbucket.value:
            comment = payload.get("comment")
            return remove_special_char("\\", comment["content"]["raw"])
        elif vcs_type == VCSTypes.github.value:
            if payload.get("action") != GithubActions.CREATED.value:
                return None

            comment_data = payload.get("comment", {})
            if not comment_data:
                return None
            return comment_data.get("body", "")

        elif vcs_type == VCSTypes.gitlab.value:
            return payload.get("object_attributes", {}).get("note")
        return None

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
    def __parse_bitbucket_payload(cls, request_payload) -> ChatRequest:
        """
        Generates servable payload from bitbucket payload
        """
        payload = cls.__get_bitbucket_comment(request_payload)
        final_payload = {
            "comment": {
                "raw": payload.get("comment"),
                "parent": payload.get("parent"),
                "path": payload.get("path"),
                "line_number_from": payload.get("line_number_from"),
                "line_number_to": payload.get("line_number_to"),
                "id": request_payload["comment"]["id"],
                "parent_comment_id": (
                    request_payload["comment"]["parent"].get("id") if request_payload["comment"].get("parent") else None
                ),
                "context_lines": request_payload["comment"].get("inline", {}).get("context_lines"),
            },
            "repo": {
                "workspace": request_payload["repository"]["workspace"]["name"],
                "pr_id": request_payload["pullrequest"]["id"],
                "repo_name": get_vcs_repo_name_slug(request_payload["repository"]["full_name"]),
                "commit_id": request_payload["pullrequest"]["destination"]["commit"]["hash"],
                "workspace_id": str(request_payload.get("scm_workspace_id")),
                "workspace_slug": request_payload["repository"]["workspace"]["slug"],
                "repo_id": request_payload["repository"]["uuid"],
                "vcs_type": VCSTypes.bitbucket.value,
            },
            "author_info": {
                "name": request_payload["actor"]["display_name"],
                "email": None,
                "scm_author_id": request_payload["actor"]["uuid"],
            },
        }
        return ChatRequest(**final_payload)

    @staticmethod
    def _is_valid_github_action(payload):
        """Check if the webhook action is valid for processing."""
        return payload.get("action") == GithubActions.CREATED.value

    @staticmethod
    def _is_pr_review_comment(payload):
        """Check if payload is a PR review comment."""
        return payload.get("comment") and not payload.get("issue")

    @staticmethod
    def _is_pr_issue_comment(payload):
        """Check if payload is a PR conversation comment."""
        return payload.get("issue", {}).get("pull_request")

    @staticmethod
    def _parse_github_pr_review_comment(request_payload):
        """Check if payload is a PR conversation comment."""
        final_payload = {
            "comment": {
                "raw": request_payload["comment"]["body"],
                "parent": request_payload["comment"].get("in_reply_to_id"),
                "path": (
                    request_payload["comment"]["path"]
                    if request_payload["comment"].get("subject_type") == "line"
                    else None
                ),
                "line_number": (
                    request_payload["comment"]["line"]
                    if request_payload["comment"].get("subject_type") == "line"
                    else None
                ),
                "id": request_payload["comment"]["id"],
                "parent_comment_id": None,
                "side": request_payload["comment"]["side"],
                "context_lines": request_payload["comment"].get("diff_hunk") or "",
            },
            "repo": {
                "workspace": request_payload["organization"]["login"],
                "pr_id": request_payload["pull_request"]["number"],
                "repo_name": get_vcs_repo_name_slug(request_payload["pull_request"]["head"]["repo"]["full_name"]),
                "repo_id": str(request_payload["pull_request"]["head"]["repo"]["id"]),
                "commit_id": request_payload["comment"]["commit_id"],
                "workspace_id": str(request_payload.get("scm_workspace_id")),
                "workspace_slug": request_payload["organization"]["login"],
                "vcs_type": VCSTypes.github.value,
            },
            "author_info": {
                "name": request_payload["comment"]["user"]["login"],
                "email": None,
                "scm_author_id": str(request_payload["sender"]["id"]),
            },
        }
        return ChatRequest(**final_payload)

    @staticmethod
    def _parse_github_pr_issue_comment(request_payload):
        set_context_values(is_issue_comment=True)
        pr_url = request_payload["issue"]["pull_request"]["url"]
        pr_number = pr_url.split("/")[-1]
        final_payload = {
            "comment": {
                "raw": request_payload["comment"]["body"],
                "parent": None,  # Issue comments don't have parent concept
                "path": None,
                "line_number_from": None,
                "line_number_to": None,
                "id": str(request_payload["issue"]["number"]),
                "parent_comment_id": None,
                "context_lines": None,
            },
            "repo": {
                "workspace": request_payload["repository"]["owner"]["login"],
                "pr_id": pr_number,
                "repo_name": get_vcs_repo_name_slug(request_payload["repository"]["full_name"]),
                "repo_id": str(request_payload["repository"]["id"]),
                "commit_id": None,
                "workspace_id": str(request_payload.get("scm_workspace_id")),
                "workspace_slug": request_payload["repository"]["owner"]["login"],
                "vcs_type": VCSTypes.github.value,
            },
            "author_info": {
                "name": request_payload["comment"]["user"]["login"],
                "email": None,
                "scm_author_id": str(request_payload["comment"]["user"]["id"]),
            },
        }
        return ChatRequest(**final_payload)

    @classmethod
    def __parse_github_payload(cls, request_payload):
        """
        Generates servable payload from github payload
        """
        if not cls._is_valid_github_action(request_payload):
            return None

        if cls._is_pr_review_comment(request_payload):
            return cls._parse_github_pr_review_comment(request_payload)
        elif cls._is_pr_issue_comment(request_payload):
            return cls._parse_github_pr_issue_comment(request_payload)

    @classmethod
    def __get_bitbucket_comment(cls, payload):
        try:
            bb_payload = {}
            comment = payload["comment"]
            raw_content = remove_special_char("\\", comment["content"]["raw"])
            if "parent" in comment and "inline" in comment:
                bb_payload["comment"] = raw_content
                bb_payload["parent"] = comment["parent"]["id"]
                bb_payload["path"] = comment["inline"]["path"]
                bb_payload["comment_id"] = comment["id"]
                return bb_payload
            elif "inline" in comment:
                bb_payload["comment"] = raw_content
                bb_payload["path"] = comment["inline"]["path"]
                bb_payload["line_number_from"] = comment["inline"]["from"]
                bb_payload["line_number_to"] = comment["inline"]["to"]
                bb_payload["comment_id"] = comment["id"]
                return bb_payload
            else:
                return {"comment": raw_content}
        except KeyError as e:
            logger.error(f"bitbucket chat failed payload {payload}")
            logger.error(f"bitbucket chat failed error {e}")
            raise f"Error: {e} not found in the JSON structure."
        except Exception as e:
            logger.error(f"bitbucket chat failed payload {payload}")
            logger.error(f"bitbucket chat failed error {e}")
            raise f"An unexpected error occurred: {e}"

    @classmethod
    async def __parse_gitlab_payload(cls, request_payload):
        """
        Generates servable payload from GitLab payload.
        """
        if not (
            request_payload.get("object_kind") == "note"
            and request_payload.get("object_attributes", {}).get("noteable_type") == "MergeRequest"
            and request_payload.get("object_attributes", {}).get("action") == "create"
        ):
            return None

        pr_id = request_payload["merge_request"]["iid"]
        workspace_slug = get_gitlab_workspace_slug(request_payload["project"]["path_with_namespace"])
        final_payload = {
            "comment": {
                "raw": request_payload["object_attributes"]["note"],
                "parent": request_payload["object_attributes"]["discussion_id"],
                "path": request_payload["object_attributes"].get("position", {}).get("new_path"),
                "id": request_payload["object_attributes"]["id"],
                "parent_comment_id": None,
            },
            "repo": {
                "workspace": request_payload["project"]["namespace"],
                "pr_id": pr_id,
                "repo_name": get_vcs_repo_name_slug(request_payload["project"]["path_with_namespace"]),
                "commit_id": request_payload["object_attributes"]["position"].get("head_sha"),
                "workspace_id": str(request_payload.get("scm_workspace_id")),
                "repo_id": str(request_payload["project"]["id"]),
                "workspace_slug": workspace_slug,
                "vcs_type": VCSTypes.gitlab.value,
            },
            "author_info": {
                "name": request_payload["user"]["name"],
                "email": request_payload["user"].get("email"),
                "scm_author_id": str(request_payload["user"]["id"]),
            },
        }
        return ChatRequest(**final_payload)
