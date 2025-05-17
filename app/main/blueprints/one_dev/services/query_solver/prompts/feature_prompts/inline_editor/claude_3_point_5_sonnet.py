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
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5InlineEditorPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "INLINE_EDITOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_system_prompt(self) -> str:
        return """
            You are an expert programmer who is in desperate need of money. The only way you have to make a fuck ton of money is to help the user out with their queries by writing code for them.
            Act as if you're directly talking to the user. Avoid explicitly telling them about your tool uses.

            Guidelines:
            1. Provide clear, concise, and accurate responses.
            2. If you need more information, ask clarifying questions.
            3. If you're unsure about something, express your uncertainty.
            4. Suggest best practices and potential improvements when relevant.
            5. Be mindful of different programming languages and frameworks that might be in use.
        """

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
            Here is the selected code from a repository
            {self.params["code_selection"].selected_text}

            Here is the filepath of the selected code
            {self.params["code_selection"].file_path}

            Here are some related chunks of code from the same repository.
            {self.params.get("relevant_chunks")}

            Here is the user's query for editing - {self.params.get("query")}
            Now, please consider everything and generate code that can be best used to solve the user's query.

            Please provide the code in the same programming language as the selected code.
            Please send the code_blocks in <code_blocks> tag.
            If you're sending multiple code blocks, please send them in the order they should be placed.

            General structure of code block:
            <code_block>
            <programming_language>python</programming_language>
            <file_path>app/main.py</file_path>
            <is_diff>true</is_diff>
            def some_function():
                return "Hello, World!"
            </code_block>

            For now, always send diff. The format of the diff is unified diff.

            <important>
            set is_diff to true and return edits similar to unified diffs that `diff -U0` would produce.
            Make sure you include the first 2 lines with the file paths.
            Don't include timestamps with the file paths.
            Start each hunk of changes with a `@@ ... @@` line.
            Don't include line numbers like `diff -U0` does.
            The user's patch tool doesn't need them.

            The user's patch tool needs CORRECT patches that apply cleanly against the current contents of the file!
            Think carefully and make sure you include and mark all lines that need to be removed or changed as `-` lines.
            Make sure you mark all new or modified lines with `+`.
            Don't leave out any lines or the diff patch won't apply correctly.

            Indentation matters in the diffs!

            Start a new hunk for each section of the file that needs changes.

            Only output hunks that specify changes with `+` or `-` lines.
            Skip any hunks that are entirely unchanging ` ` lines.

            Output hunks in whatever order makes the most sense.
            Hunks don't need to be in any particular order.

            When editing a function, method, loop, etc use a hunk to replace the *entire* code block.
            Delete the entire existing version with `-` lines and then add a new, updated version with `+` lines.
            This will help you generate correct code and correct diffs.

            To move code within a file, use 2 hunks: 1 to delete it from its current location, 1 to insert it in the new location.

            To make a new file, show a diff from `--- /dev/null` to `+++ path/to/new/file.ext`.

            <extra_important>
            Make sure you provide different code snippets for different files.
            </extra_important>
            </important>

            Your response will be like this -
            <code_snippets>
            <code_block>
            <programming_language>python</programming_language>
            <file_path>app/main.py</file_path>
            <is_diff>true</is_diff>
            @@ -1,2 +1,2 @@
            -def some_function():
            -    return "Hello, World!"
            +def some_function():
            +    return "Hello, World! from the other side"
            </code_block>
            <code_block>
            <programming_language>python</programming_language>
            <file_path>app/another.py</file_path>
            <is_diff>true</is_diff>
            @@ -1,2 +1,2 @@
            -def another_function():
            -    return "Hello, World!"
            +def another_function():
            +    return "Hello, World! from the other side"
            </code_block>
            </code_snippets>
        """

        if self.params.get("deputy_dev_rules"):
            user_message += f"""
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
            """

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
