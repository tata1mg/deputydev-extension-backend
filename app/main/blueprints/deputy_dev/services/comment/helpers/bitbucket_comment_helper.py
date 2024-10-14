import re

from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import (
    extract_line_number_from_llm_response,
    format_comment,
)


class BitbucketCommentHelper:
    @classmethod
    def format_pr_review_comment(cls, comment) -> dict:
        file_path = comment.get("file_path")
        comment_payload = {"content": {"raw": format_comment(comment)}}

        if isinstance(file_path, str) and file_path:
            sanitized_file_path = re.sub(r"^[ab]/\s*", "", file_path).split(",")[0]

            comment_payload["inline"] = {
                "path": (
                    re.sub(r"^[ab]/\s*", "", sanitized_file_path)
                    if re.match(r"^[ab]/\s*", sanitized_file_path)
                    else file_path
                )
            }
        line_number = extract_line_number_from_llm_response(comment.get("line_number"))
        if line_number is not None:
            if line_number >= 0:
                comment_payload["inline"]["to"] = line_number
            else:
                comment_payload["inline"]["from"] = abs(line_number)
        return comment_payload

    @classmethod
    def format_chat_comment(cls, comment, chat_request: ChatRequest) -> dict:
        comment_payload = {
            "comment": comment,
            "file_path": chat_request.comment.path,
            "line_number_from": chat_request.comment.line_number_from,
            "line_number_to": chat_request.comment.line_number_to,
        }
        return comment_payload

    @classmethod
    def format_chat_thread_comment(cls, comment, chat_request: ChatRequest) -> dict:
        comment_payload = {
            "content": {"raw": format_comment(comment)},
            "parent": {"id": chat_request.comment.parent},
            "inline": {"path": chat_request.comment.path},
        }
        return comment_payload

    @classmethod
    def format_pr_review_inline_comment(cls, comment) -> dict:
        if comment.get("file_path"):
            comment["file_path"] = re.sub(r"^[ab]/\s*", "", comment["file_path"])
        comment_payload = {
            "content": {"raw": format_comment(comment)},
            "inline": {
                "path": (
                    re.sub(r"^[ab]/\s*", "", comment["file_path"])
                    if re.match(r"^[ab]/\s*", comment.get("file_path"))
                    else comment.get("file_path")
                ),
            },
        }
        if comment["line_number_from"]:
            comment_payload["inline"]["from"] = comment["line_number_from"]
        else:
            comment_payload["inline"]["to"] = comment["line_number_to"]
        return comment_payload
