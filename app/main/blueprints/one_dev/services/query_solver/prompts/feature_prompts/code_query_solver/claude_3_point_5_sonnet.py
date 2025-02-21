from typing import Any, AsyncIterator, Coroutine, Dict, List, Optional

from app.backend_common.services.llm.dataclasses.main import (
    ContentBlockCategory,
    NonStreamingResponse,
    NonStreamingTextBlock,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5CodeQuerySolverPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "CODE_QUERY_SOLVER"

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest. As an expert programmer, your task is to assist users with coding-related questions. Analyze the provided code context carefully and use it to inform your responses. If the context is insufficient, draw upon your general programming knowledge to provide accurate and helpful advice.

            Guidelines:
            1. Provide clear, concise, and accurate responses.
            2. If you need more information, ask clarifying questions.
            3. If you're unsure about something, express your uncertainty.
            4. Suggest best practices and potential improvements when relevant.
            5. Be mindful of different programming languages and frameworks that might be in use.
            """

        user_message = f"""
            Here are some chunks of code from a repository:
            {self.params.get("relevant_chunks")}

            The user has given a query for the same repo as follows:
            User Query: {self.params.get("query")}

            Please think through the query and generate a plan to implement the same. Return the plan in <thinking> tag.

            Now, think of what code snippets can be prepared from the given context and what all extra context you need.
            Also, please use the tools provided to ask the user for any additional information required.
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: NonStreamingTextBlock) -> Dict[str, Any]:
        final_query_resp: Optional[str] = None
        is_task_done: Optional[bool] = None
        summary: Optional[str] = None
        text_block_text = text_block.content.text.strip()
        if "<response>" in text_block_text:
            final_query_resp = text_block_text.split("<response>")[1].split("</response>")[0].strip()
        if "<is_task_done>true</is_task_done>" in text_block_text:
            is_task_done = True
        if "<summary>" in text_block_text:
            summary = text_block_text.split("<summary>")[1].split("</summary>")[0].strip()

        if final_query_resp and is_task_done is not None:
            return {"response": final_query_resp, "is_task_done": is_task_done, "summary": summary}
        raise ValueError("Invalid LLM response format. Response not found.")

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:

        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                final_content.append({"tool_use_request": content_block.content.model_dump(mode="json")})
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content

    @classmethod
    def get_parsed_streaming_events(
        cls, llm_response: StreamingResponse
    ) -> Coroutine[Any, Any, AsyncIterator[Dict[str, Any]]]:
        pass
