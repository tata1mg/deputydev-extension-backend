import re
from typing import Any, Dict

from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import (
    extract_line_number_from_llm_response,
    format_comment,
)


class GithubCommentHelper:
    @classmethod
    def format_pr_review_comment(cls, comment: Dict[str, Any]) -> Dict[str, Any]:
        file_path = comment.get("file_path")
        comment_payload: Dict[str, Any] = {
            "body": format_comment(comment),
            "commit_id": comment["commit_id"],
        }
        if isinstance(file_path, str) and file_path:
            sanitized_file_path = re.sub(r"^[ab]/\s*", "", file_path).split(",")[0]
            comment_payload["path"] = (
                re.sub(r"^[ab]/\s*", "", sanitized_file_path)
                if re.match(r"^[ab]/\s*", sanitized_file_path)
                else file_path
            )
        line_number = extract_line_number_from_llm_response(comment.get("line_number"))
        if line_number is not None:
            comment_payload["line"] = line_number
            if line_number >= 0:
                comment_payload["side"] = "RIGHT"
            else:
                comment_payload["side"] = "LEFT"

        if comment.get("in_reply_to_id"):
            comment_payload["in_reply_to"] = comment["in_reply_to_id"]
        return comment_payload

    @classmethod
    def format_chat_comment(cls, comment: str, chat_request: ChatRequest, have_parent: bool) -> Dict[str, Any]:
        comment_payload: Dict[str, Any] = {
            "body": comment,
            "path": chat_request.comment.path,
            "line": chat_request.comment.line_number,
            "side": chat_request.comment.side,
            "commit_id": chat_request.repo.commit_id,
        }
        if have_parent:
            comment_payload["in_reply_to"] = chat_request.comment.parent
        return comment_payload

    @classmethod
    def format_chat_thread_comment(cls, comment: str, chat_request: ChatRequest) -> Dict[str, Any]:
        comment_payload: Dict[str, Any] = {
            "content": comment,
            "in_reply_to_id": chat_request.comment.parent,
            "path": chat_request.comment.path,
            "side": chat_request.comment.side,
        }
        return comment_payload
