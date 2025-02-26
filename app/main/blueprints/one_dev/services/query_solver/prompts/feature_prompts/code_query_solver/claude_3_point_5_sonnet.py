import re
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageData,
    TextBlockData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    TextBlockDelta,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)
from app.backend_common.services.llm.providers.anthropic.prompts.parsers.event_based.text_block_xml_parser import (
    BaseAnthropicTextDeltaParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockDeltaContent,
    CodeBlockEnd,
    CodeBlockStart,
    CodeBlockStartContent,
    ThinkingBlockDelta,
    ThinkingBlockDeltaContent,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)


class ThinkingParser(BaseAnthropicTextDeltaParser):
    def __init__(self):
        super().__init__(xml_tag="thinking")

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:
        if not self.start_event_completed:
            self.event_buffer.append(ThinkingBlockStart())
            self.start_event_completed = True

        if event.content.text:
            self.event_buffer.append(
                ThinkingBlockDelta(content=ThinkingBlockDeltaContent(thinking_delta=event.content.text))
            )

        if last_event:
            self.event_buffer.append(ThinkingBlockEnd())

        values_to_return = self.event_buffer
        self.event_buffer = []
        return values_to_return


class CodeBlockParser(BaseAnthropicTextDeltaParser):
    def __init__(self):
        super().__init__(xml_tag="code_block")

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:

        self.text_buffer += event.content.text

        programming_language_block = re.search(r"<programming_language>(.*?)</programming_language>", self.text_buffer)
        file_path_block = re.search(r"<file_path>(.*?)</file_path>", self.text_buffer)
        if programming_language_block and file_path_block:
            self.event_buffer.append(
                CodeBlockStart(
                    content=CodeBlockStartContent(
                        language=programming_language_block.group(1), filepath=file_path_block.group(1), is_diff=False
                    )
                )
            )
            self.text_buffer = self.text_buffer.replace(programming_language_block.group(0), "").replace(
                file_path_block.group(0), ""
            )
            self.start_event_completed = True

        if self.start_event_completed and self.text_buffer:
            self.event_buffer.append(CodeBlockDelta(content=CodeBlockDeltaContent(code_delta=self.text_buffer)))
            self.text_buffer = ""

        if last_event:
            self.event_buffer.append(CodeBlockEnd())

        values_to_return = self.event_buffer
        self.event_buffer = []
        return values_to_return


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
            If you can provide some code snippets, make sure to return them in the <code_block> tag.
            Write the code_block in the following format:
            <code_block>
            <programming_language>python</programming_language>
            <file_path>app/main.py</file_path>
            def some_function():
                return "Hello, World!"
            </code_block>

            Also, please use the tools provided to ask the user for any additional information required.
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
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
    def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[Dict[str, Any]]:
        final_content = []
        for block in response_block:
            if block.type == "TOOL_USE_RESPONSE":
                final_content.append({
                    "type": "TOOL_USE_RESPONSE_BLOCK",
                    "content": {
                        "result_json": block.content.response,
                        "tool_use_id": block.content.tool_use_id
                    }
                })
            elif block.type == "TEXT_BLOCK":
                final_content.extend(cls.parsing(block.content.text))
            elif block.type == "TOOL_USE_REQUEST":
                final_content.append({
                    "type": "TOOL_USE_REQUEST_BLOCK",
                    "content": {
                        "tool_name": block.content.tool_name,
                        "tool_use_id": block.content.tool_use_id,
                        "tool_input_json": block.content.tool_input
                    }
                })
        return final_content

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:

        final_content: List[Dict[str, Any]] = []

        final_content = cls.get_parsed_response_blocks(llm_response.content)

        # for content_block in llm_response.content:
        #     if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
        #         final_content.append({"tool_use_request": content_block.content.model_dump(mode="json")})
        #     elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
        #         final_content.append(cls._parse_text_block(content_block))

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        return cls.parse_streaming_text_block_events(
            events=llm_response.content, parsers=[ThinkingParser(), CodeBlockParser()]
        )

    @classmethod
    def parsing(cls, input_string: str) -> List[Dict[str, Any]]:
        result = []

        # Define the patterns
        thinking_pattern = r'<thinking>(.*?)</thinking>'
        code_block_pattern = r'<code_block>(.*?)</code_block>'

        # Find all occurrences of either pattern
        matches_thinking = re.finditer(thinking_pattern, input_string, re.DOTALL)
        matches_code_block = re.finditer(code_block_pattern, input_string, re.DOTALL)

        # Combine matches and sort by start position
        matches = list(matches_thinking) + list(matches_code_block)
        matches.sort(key=lambda match: match.start())

        last_end = 0
        for match in matches:
            start_index = match.start()
            end_index = match.end()

            if start_index > last_end:
                text_before = input_string[last_end:start_index]
                if text_before.strip():  # Only append if not empty
                    result.append({"type": "TEXT_BLOCK", "content": {"text": text_before.strip()}})

            if match.re.pattern == code_block_pattern:
                code_block_string = match.group(1).strip()
                code_block_info = cls.extract_code_block_info(code_block_string)
                result.append({"type": "CODE_BLOCK", "content": code_block_info})
            elif match.re.pattern == thinking_pattern:
                result.append({"type": "THINKING_BLOCK", "content": {"text": match.group(1).strip()}})

            last_end = end_index

        # Append any remaining text
        if last_end < len(input_string):
            remaining_text = input_string[last_end:]
            if remaining_text.strip():  # Only append if not empty
                result.append({"type": "TEXT_BLOCK", "content": {"text": remaining_text.strip()}})

        return result

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, str]:
        if not code_block_string:
            return {}

        # Define the patterns
        language_pattern = r'<programming_language>(.*?)</programming_language>'
        file_path_pattern = r'<file_path>(.*?)</file_path>'

        # Extract language and file path
        language_match = re.search(language_pattern, code_block_string)
        file_path_match = re.search(file_path_pattern, code_block_string)

        language = language_match.group(1) if language_match else ""
        file_path = file_path_match.group(1) if file_path_match else ""

        # Extract code
        code_start_index = file_path_match.end() if file_path_match else 0
        code = code_block_string[code_start_index:].strip()

        # Remove any remaining tags from the code
        code = re.sub(r'<.*?>', '', code)

        return {
            "language": language,
            "file_path": file_path,
            "code": code
        }