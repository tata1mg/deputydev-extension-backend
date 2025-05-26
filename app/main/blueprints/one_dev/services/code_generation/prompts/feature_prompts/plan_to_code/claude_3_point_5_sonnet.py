from typing import Any, Dict, List

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.base_claude_3_point_5_sonnet_prompt_handler import (
    BaseClaude3Point5SonnetPromptHandler,
)


class Claude3Point5PlanCodeGenerationPrompt(BaseClaude3Point5SonnetPromptHandler):
    prompt_type = "PLAN_CODE_GENERATION"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
                You are a code expert, and have created a plan for some code generation task. You are now asked to implement the plan.
            """

        user_message = """
            Please check the previous responses, and take into context the relevant chunks that you heve been provided in the first conversation.
            Now, based on the plan you have previously generated and the chunks you have been provided, please implement the relevant code.

            Please respond in the following format:
            <response>
            Your response here
            </response>
            <summary>
            Please return a short summary of response. Please include function, classes and files names which are part of response specifically.
            </summary>
            <is_task_done>true</is_task_done>
            Please put your entire response within the <response> tag.
            Set the <is_task_done> tag to true if you have responded correctly.
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        raw_text = text_block.content.text
        final_query_resp = None
        is_task_done = None
        summary = None
        if "<response>" in raw_text:
            final_query_resp = raw_text.split("<response>")[1].split("</response>")[0].strip()
        if "<is_task_done>true</is_task_done>" in raw_text:
            is_task_done = True
        if "<summary>" in raw_text:
            summary = raw_text.split("<summary>")[1].split("</summary>")[0].strip()
        if final_query_resp and is_task_done is not None:
            return {"response": final_query_resp, "is_task_done": is_task_done, "summary": summary}
        raise ValueError("Invalid LLM response format. Response not found.")

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content
