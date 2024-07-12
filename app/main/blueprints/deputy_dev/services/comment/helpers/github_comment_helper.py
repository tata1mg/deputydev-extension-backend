import re

from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import format_comment


class GithubCommentHelper:
    @classmethod
    def format_pr_review_comment(cls, comment) -> dict:
        comment["file_path"] = re.sub(r"^[ab]/\s*", "", comment["file_path"])
        comment_payload = {
            "body": format_comment(comment),
            "path": re.sub(r"^[ab]/\s*", "", comment["file_path"])
            if re.match(r"^[ab]/\s*", comment.get("file_path"))
            else comment.get("file_path"),
            "start_side": "RIGHT",
            "commit_id": comment["commit_id"],
        }
        if int(comment.get("line_number")) >= 0:
            comment_payload["line"] = int(comment.get("line_number"))
        else:
            comment_payload["line"] = -1 * int(comment.get("line_number"))
        if comment.get("in_reply_to_id"):
            comment_payload["in_reply_to"] = comment["in_reply_to_id"]
        return comment_payload

    @classmethod
    def format_chat_comment(cls, comment, chat_request: ChatRequest):
        comment_payload = {
            "comment": comment,
            "file_path": chat_request.comment.path,
            "line_number": chat_request.comment.line_number,
            "in_reply_to_id": chat_request.comment.parent,
        }
        return comment_payload
