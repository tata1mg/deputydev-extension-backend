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


class Claude3Point5IterativeCodeChatPrompt(BaseClaude3Point5SonnetPromptHandler):
    prompt_type = "ITERATIVE_CODE_CHAT"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
                You are a code expert, and asked a question by the user. You need to respond to the user query based on the context of the conversation.
                Please generate code snippets, explanations, or any other relevant information to help the user with their query.
                Remember to:
                - Write actual implementation code, not just pseudocode the code can be copied and used directly.
                - Please follow the project's existing code writing pattern.
                - Keep the tests focused and maintainable.
                - Include necessary imports and setup.
                - Use inline comments where ever required for understanding code better.
            """

        user_message = f"""
            Please handle the user query on your last response : {self.params.get("query")}

            Relevant Code Context from the repository for the asked question:
            {self.params.get("relevant_chunks")}

            Please respond in the following format:
            <response>
            Your response here
            </response>
            <is_task_done>true</is_task_done>
            <summary>
            Please return a short summary of response. Please include function, classes and files names which are part of response specifically.
            </summary>
            Please put your entire response within the <response> tag.
            Set the <is_task_done> tag to true if you have responded correctly.
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        llm_response = text_block.content.text
        final_query_resp = None
        is_task_done = None
        summary = None
        if "<response>" in llm_response:
            final_query_resp = llm_response.split("<response>")[1].split("</response>")[0].strip()
        if "<is_task_done>true</is_task_done>" in llm_response:
            is_task_done = True
        if "<summary>" in llm_response:
            summary = llm_response.split("<summary>")[1].split("</summary>")[0].strip()

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
