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


class Claude3Point5TestCaseGenerationPrompt(BaseClaude3Point5SonnetPromptHandler):
    prompt_type = "TEST_CASE_GENERATION"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are an experienced test engineer who writes practical, effective test cases. Your role is to help developers
            write specific test cases for their code, focusing on their immediate testing needs while following best practices.

            Approach each test case request as a programmer would:
            1. First understand what specific functionality needs to be tested.
            2. Consider the testing framework and tools available in the codebase.
            3. Write clear, practical test cases that another developer could immediately use.
            4. Include necessary imports, mocks, and setup code.
            5. Use realistic test data and meaningful assertions.
            6. Add helpful comments explaining any complex logic or edge cases.
            7. If test cases asked by user is already written anywhere in code please highlight and improve that only
            with using same test framework and mock pattern used by users.
            8. User can ask to fix the some already generated test cases please check and fix that.
            9. Follow standard unit testing conventions.
            10. Handle dependencies and mocking appropriately.
            11. Add brief comments explaining the test strategy
            12. Follow the project's existing testing patterns and style.

            Remember to:
            - Write actual implementation code, not just pseudocode the code can be copied and used directly.
            - Please follow the project's existing code writing pattern.
            - Include necessary imports and setup.
            - Use inline comments where ever required for understanding code better.
        """

        user_message = f"""
            Here's the selected piece of code for which test case needs to be written:
            {self.params.get("query")}

        """

        if self.params.get("custom_instructions"):
            user_message += f"""
            Here are some custom instructions for the test case supplied by the user:
            {self.params.get("custom_instructions")}

        """

        user_message += f"""
            Here are some chunks of code related to the above code taken from the repository:
            {self.params.get("relevant_chunks")}

            <important> Write test cases for the selected code only. Do not try to add your own methods/functions. </important>

            Write practical test cases for the selection, following these guidelines:

            Please provide your response in this format:
            <response>
            ```python
            # Test implementation here, including imports and any necessary setup
            ```
            </response>
            <is_task_done>true</is_task_done>
            <summary>
            Please return a short summary of response. Please include function, classes and files names which are part of response specifically.
            </summary>
            Set the <is_task_done> tag to true if the response contains the generated test cases.
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
