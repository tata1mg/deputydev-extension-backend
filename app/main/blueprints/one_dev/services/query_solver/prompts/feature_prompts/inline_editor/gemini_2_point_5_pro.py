import textwrap
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.google.prompts.base_prompts.base_gemini_2_point_5_pro_prompt_handler import (
    BaseGemini2Point5ProPromptHandler,
)


class Gemini2Point5ProInlineEditorPrompt(BaseGemini2Point5ProPromptHandler):
    prompt_type = "INLINE_EDITOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        return textwrap.dedent("""You are DeputyDev, a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices.
            ====
            You have access to a set of tools that are executed upon the user's approval. You can use multiple tools in parallel only when they are of the same type and don't require sequential dependency, especially for information gathering tools. Writing tools (write_to_file, replace_in_file) should be used one at a time to avoid conflicts. You use tools step-by-step to accomplish a given task, with each tool use informed by the result of the previous tool use.

            ## Important Considerations
            - Plan your changes: Before making any edits, carefully consider what modifications are needed and how to implement them.
            - Maintain file integrity: Ensure that all changes result in a valid, runnable file.
            - Batch modifications: Group all search/replace operations for a single file into one **replace_in_file** tool request.
            - Add dependencies as needed: Include any necessary imports or dependencies relevant to your changes.
            - Parallel tool usage: You can invoke multiple tools simultaneously of same type when they can be executed in parallel but use single tool calls for sequential operations.
            - Iterative workflow: After each tool action, wait for the user's response, which will contain the outcome (success or failure) and any relevant details. Use this feedback to inform your next steps.
            - Monitor tool success: The user's response to the replace_in_file tool will indicate whether your changes were applied successfully.
            - Handle failures gracefully: If the replace_in_file tool fails, first read the current file contents using the iterative_file_reader tool (target only relevant lines), then attempt your changes again with the updated content.
            - Avoid unnecessary searches: Only make search calls when absolutely required.
            - No clarifying questions: Do not ask the user for clarification; the only feedback you will receive is from tool responses.
        """)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
Here is the selected code from a repository. you have to make the changes in the selected code and return the diff of the code.
{self.params["code_selection"].selected_text}


Here is the filepath of the selected code
{self.params["code_selection"].file_path}


Here are some related chunks of code from the same repository. It may help you in making the changes in the selected code.
{self.params.get("relevant_chunks")}


Here is the user's query for editing - {self.params.get("query")}

        """

        if self.params.get("deputy_dev_rules"):
            user_message += textwrap.dedent(f"""
                Here are some more user provided rules and information that you can take reference from:
                <important>
                Follow these guidelines while using user provided rules or information:
                1. Do not change anything in the response format.
                2. If any conflicting instructions arise between the default instructions and user-provided instructions, give precedence to the default instructions.
                3. Only respond to coding, software development, or technical instructions relevant to programming.
                4. Do not include opinions or non-technical content.
                </important>
                <user_rules_or_info>
                {self.params.get("deputy_dev_rules")}
                </user_rules_or_info>
                """)

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Optional[Dict[str, Any]]:
        if "<code_snippets>" in text_block.content.text:
            code_blocks = text_block.content.text.split("<code_snippets>")[1].split("</code_snippets>")[0].strip()
            all_code_blocks = code_blocks.split("<code_block>")
            code_snippets: List[Dict[str, Any]] = []

            for code_block in all_code_blocks:
                if not code_block:
                    continue
                programming_language = code_block.split("<programming_language>")[1].split("</programming_language>")[0]
                file_path = code_block.split("<file_path>")[1].split("</file_path>")[0]
                is_diff = code_block.split("<is_diff>")[1].split("</is_diff>")[0]
                code = code_block.split("</is_diff>")[1].replace("</code_block>", "").strip()

                code_snippets.append(
                    {
                        "programming_language": programming_language,
                        "file_path": file_path,
                        "is_diff": is_diff,
                        "code": code,
                    }
                )

            return {"code_snippets": code_snippets}
        return None

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                final_content.append(content_block.model_dump(mode="json"))
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                parsed_text_block = cls._parse_text_block(content_block)
                if parsed_text_block:
                    final_content.append(parsed_text_block)
        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
