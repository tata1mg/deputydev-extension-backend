# flake8: noqa
from app.main.blueprints.deputy_dev.constants.prompts.v2.system_prompts import (
    CHAT_COMMENT_PROMPT,
)
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import append_line_numbers


class ChatPromptService:
    @classmethod
    def build_chat_prompt(cls, pr_diff, user_story, comment_thread, chat_request: ChatRequest):
        system_prompt = cls.__build_system_prompt()
        pr_diff = append_line_numbers(pr_diff)
        question_info = {
            "raw": chat_request.comment.raw,
            "line_number": f"+{chat_request.comment.line_number_to}"
            if chat_request.comment.line_number_to
            else f"-{chat_request.comment.line_number_from}",
            "file_path": chat_request.comment.path,
        }
        user_prompt = cls.__build_user_prompt(pr_diff, question_info, user_story, comment_thread)
        return system_prompt, user_prompt

    @classmethod
    def __build_system_prompt(cls):
        return CHAT_COMMENT_PROMPT

    @classmethod
    def __build_user_prompt(cls, pr_diff, question_info, user_story, comment_thread):
        return f"""
        <pr_diff>
        {pr_diff}
        </pr_diff>
        
        <question>
        query: {question_info["raw"]}
        line_number: {question_info.get("line_number", "Not available") }
        file_path: {question_info.get("line_number", "Not available")}
        </question>
        
         <user_story>
        {user_story or "Not available"}
        </user_story>
        
        <comment_thread>
        {comment_thread or "Not available"}
        </comment_thread>   
        """
