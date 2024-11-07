# flake8: noqa
from app.main.blueprints.deputy_dev.constants.prompts.v2.system_prompts import (
    CHAT_COMMENT_PROMPT_LINE,
    CHAT_COMMENT_PROMPT_WHOLE_PR,
)
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.utils import append_line_numbers


class ChatPromptService:
    @classmethod
    def build_chat_prompt(cls, pr_diff, user_story, comment_thread, chat_request: ChatRequest):
        pr_diff = append_line_numbers(pr_diff)
        question_info = {
            "raw": chat_request.comment.raw,
            "line_number": (
                f"+{chat_request.comment.line_number_to}"
                if chat_request.comment.line_number_to
                else f"-{chat_request.comment.line_number_from}"
            ),
            "file_path": chat_request.comment.path,
            "context_lines": append_line_numbers(chat_request.comment.context_lines),
        }
        is_inline_question = question_info.get("file_path") is not None
        system_prompt = cls.__build_system_prompt(is_inline_question)
        user_prompt = cls.__build_user_promptr(is_inline_question, pr_diff, question_info, user_story, comment_thread)
        return system_prompt, user_prompt

    @classmethod
    def __build_system_prompt(cls, is_line_specific_question):
        return CHAT_COMMENT_PROMPT_LINE if is_line_specific_question else CHAT_COMMENT_PROMPT_WHOLE_PR

    @classmethod
    def __build_user_promptr(cls, is_line_specific_question, pr_diff, question_info, user_story, comment_thread):
        return (
            cls.__build_user_prompt_line(pr_diff, question_info, user_story, comment_thread)
            if is_line_specific_question
            else cls.__build_user_prompt_whole_pr(pr_diff, question_info, user_story, comment_thread)
        )

    @classmethod
    def __build_user_prompt_whole_pr(cls, pr_diff, question_info, user_story, comment_thread):
        prompt = f"""
        <question>{question_info["raw"]}</question>
        <pr_diff>
        {pr_diff}
        </pr_diff>
        """
        if user_story:
            prompt += f"""<user_story>
                   {user_story or "Not available"}
                   </user_story>"""

        if comment_thread:
            prompt += f"""
                    <comment_thread>
                   {comment_thread or "Not available"}
                   </comment_thread>   
                   """
        return prompt

    @classmethod
    def __build_user_prompt_line(cls, pr_diff, question_info, user_story, comment_thread):
        prompt = f"""
        Question info
        <question>{question_info["raw"]}</question>
        <line_number>{question_info["line_number"]}</line_number>
        <file_path>{question_info.get("file_path")}</file_path> 
        <context_lines>{question_info.get("context_lines")}</context_lines>
        Please make sure to answer on asked file and line only.
        
        Context info:
        <pr_diff>
        {pr_diff}
        </pr_diff>
        """
        if user_story:
            prompt += f"""<user_story>
            {user_story or "Not available"}
            </user_story>"""

        if comment_thread:
            prompt += f"""
             <comment_thread>
            {comment_thread or "Not available"}
            </comment_thread>   
            """
        return prompt
