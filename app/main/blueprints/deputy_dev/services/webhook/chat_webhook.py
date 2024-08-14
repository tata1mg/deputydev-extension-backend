from app.common.utils.app_utils import get_bitbucket_repo_name_slug
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import remove_special_char


class ChatWebhook:
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
                "parent_comment_id": request_payload["comment"]["parent"].get("id")
                if request_payload["comment"].get("parent")
                else None,
            },
            "repo": {
                "workspace": request_payload["repository"]["workspace"]["slug"],
                "pr_id": request_payload["pullrequest"]["id"],
                "repo_name": get_bitbucket_repo_name_slug(request_payload["repository"]["full_name"]),
                "commit_id": request_payload["pullrequest"]["destination"]["commit"]["hash"],
                "workspace_id": request_payload["repository"]["workspace"]["uuid"],
            },
            "author_info": {
                "name": request_payload["actor"]["display_name"],
                "email": None,
                "scm_author_id": request_payload["actor"]["uuid"],
            },
        }
        return ChatRequest(**final_payload)

    @classmethod
    def __parse_github_payload(cls, request_payload) -> ChatRequest:
        """
        Generates servable payload from github payload
        """
        final_payload = {
            "comment": {
                "raw": request_payload["comment"]["body"],
                "parent": request_payload["comment"].get("in_reply_to_id"),
                "path": request_payload["comment"]["path"]
                if request_payload["comment"].get("subject_type") == "line"
                else None,
                "line_number": request_payload["comment"]["line"]
                if request_payload["comment"].get("subject_type") == "line"
                else None,
                "id": request_payload["comment"]["id"],
                "parent_comment_id": None,
            },
            "repo": {
                "workspace": request_payload["pull_request"]["head"]["repo"]["owner"]["login"],
                "pr_id": request_payload["pull_request"]["number"],
                "repo_name": request_payload["pull_request"]["head"]["repo"]["name"],
                "commit_id": request_payload["comment"]["commit_id"],
                "workspace_id": str(request_payload["organization"]["id"]),
            },
            "author_info": {
                "name": request_payload["comment"]["user"]["login"],
                "email": None,
                "scm_author_id": str(request_payload["sender"]["id"]),
            },
        }
        return ChatRequest(**final_payload)

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
            raise f"Error: {e} not found in the JSON structure."
        except Exception as e:
            raise f"An unexpected error occurred: {e}"
