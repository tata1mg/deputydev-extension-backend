from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5CodeGenerationPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "CODE_GENERATION"

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest. As an expert programmer, your task is to assist users with coding-related questions. Analyze the provided code context carefully and use it to inform your responses. If the context is insufficient, draw upon your general programming knowledge to provide accurate and helpful advice.

            Guidelines:
            1. Provide clear, concise, and accurate responses.
            2. If you need more information, ask clarifying questions.
            3. Explain your reasoning and provide code examples when appropriate.
            4. If you're unsure about something, express your uncertainty.
            5. Suggest best practices and potential improvements when relevant.
            6. Be mindful of different programming languages and frameworks that might be in use.
            """

        user_message = f"""
            Relevant Code Context from the repository:
            {self.params.get("relevant_chunks")}

            User Query: {self.params.get("query")}

            Please provide working code which would solve the above mentioned user query.

            Please provide the response in the following format:
            <response>
            Your response here
            </response>
            <is_task_done>true</is_task_done>
            <summary>
            Please return a short summary of response. Please include function, classes and files names which are part of response specifically.
            </summary>
            Please put your entire response within the <response> tag and set the <is_task_done> tag to true if the response contains generated code.
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
