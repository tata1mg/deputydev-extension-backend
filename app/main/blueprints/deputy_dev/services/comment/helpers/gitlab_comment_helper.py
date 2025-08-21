import re
from typing import Any, Dict

from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import (
    extract_line_number_from_llm_response,
    format_comment,
)


class GitlabCommentHelper:
    @classmethod
    def format_pr_review_comment(cls, comment: Dict[str, Any], diff_refs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats a comment for reviewing a GitLab merge request.
        """
        file_path = comment.get("file_path")
        position = {"position_type": "text"}
        position.update(diff_refs)
        comment_payload = {"body": format_comment(comment), "position": position}  # GitLab uses 'note' for comment body

        if isinstance(file_path, str) and file_path:
            sanitized_file_path = re.sub(r"^[ab]/\s*", "", file_path).split(",")[0]
            filtered_file_path = (
                re.sub(r"^[ab]/\s*", "", sanitized_file_path)
                if re.match(r"^[ab]/\s*", sanitized_file_path)
                else file_path
            )
            comment_payload["position"]["new_path"] = filtered_file_path
            comment_payload["position"]["old_path"] = filtered_file_path

        # GitLab handles lines in a diff differently
        line_number = extract_line_number_from_llm_response(comment.get("line_number"))
        if line_number is not None:
            # GitLab uses new_line for comments on new content, old_line for old content
            if line_number >= 0:
                comment_payload["position"]["new_line"] = line_number
            else:
                comment_payload["position"]["old_line"] = abs(line_number)

        comment_payload["commit_id"] = comment["commit_id"]

        return comment_payload

    @classmethod
    def format_chat_thread_comment(cls, comment: str, chat_request: ChatRequest) -> Dict[str, Any]:
        """
        Formats a comment reply in a thread for GitLab.
        """
        comment_payload = {
            "note": comment,
            "in_reply_to": chat_request.comment.parent,
            "path": chat_request.comment.path,
        }

        if chat_request.comment.line_number is not None:
            if chat_request.comment.side == "RIGHT":
                comment_payload["new_line"] = chat_request.comment.line_number
            else:
                comment_payload["old_line"] = abs(chat_request.comment.line_number)

        return comment_payload
