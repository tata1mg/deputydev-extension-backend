import re
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import (
    MessageData,
    TextBlockData,
    ToolUseRequestData,
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
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    FocusItemTypes,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockDeltaContent,
    CodeBlockEnd,
    CodeBlockEndContent,
    CodeBlockStart,
    CodeBlockStartContent,
    SummaryBlockDelta,
    SummaryBlockDeltaContent,
    SummaryBlockEnd,
    SummaryBlockStart,
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


class SummaryParser(BaseAnthropicTextDeltaParser):
    def __init__(self):
        super().__init__(xml_tag="summary")

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:
        if not self.start_event_completed:
            self.event_buffer.append(SummaryBlockStart())
            self.start_event_completed = True

        if event.content.text:
            self.event_buffer.append(
                SummaryBlockDelta(content=SummaryBlockDeltaContent(summary_delta=event.content.text))
            )

        if last_event:
            self.event_buffer.append(SummaryBlockEnd())

        values_to_return = self.event_buffer
        self.event_buffer = []
        return values_to_return


class CodeBlockParser(BaseAnthropicTextDeltaParser):
    def __init__(self):
        super().__init__(xml_tag="code_block")
        self.diff_buffer = ""
        self.udiff_line_start: Optional[str] = None
        self.is_diff: Optional[bool] = None
        self.diff_line_buffer = ""
        self.added_lines = 0
        self.removed_lines = 0
        self.first_data_block_sent = False

    def find_newline_instances(self, input_string: str) -> List[Tuple[int, int]]:
        # Regular expression to match either \n or \r\n
        pattern = r"\r?\n"

        # Find all matches
        matches = [(m.start(), m.end()) for m in re.finditer(pattern, input_string)]

        return matches

    async def _get_udiff_line_start(self, line_data: str) -> Optional[str]:
        if line_data.startswith("@@"):
            return "@@"
        if line_data.startswith("---"):
            return "---"
        if line_data.startswith("+++"):
            return "+++"
        if line_data.startswith(" "):
            return " "
        if line_data.startswith("+"):
            return "+"
        if line_data.startswith("-"):
            return "-"
        return None

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:
        if self.is_diff is None:
            self.text_buffer += event.content.text
        elif self.is_diff:
            self.diff_line_buffer += event.content.text
            self.diff_buffer += event.content.text
            if self.udiff_line_start:
                # end current udiff line if we have reached the end of the line
                # in case the line buffer contains a newline character
                newline_instances = self.find_newline_instances(self.diff_line_buffer)
                while newline_instances:
                    start, end = newline_instances.pop(0)
                    pre_line_part = self.diff_line_buffer[:start]
                    self.diff_line_buffer = self.diff_line_buffer[end:]
                    newline_instances = self.find_newline_instances(self.diff_line_buffer)
                    if self.udiff_line_start in [" ", "+"]:
                        self.text_buffer += (
                            pre_line_part.replace(f"{self.udiff_line_start}", "", 1) + "\n"
                        )  # replace only the first instance of the udiff line start
                        if self.udiff_line_start == "+":
                            self.added_lines += 1
                    # if self.udiff_line_start == "@@":
                    #     # skip till the last @@ in the line and add the line to the text buffer
                    #     last_index = pre_line_part.rfind("@@")
                    #     addable_part = pre_line_part[last_index + 3 :]  # to handle last '@@ '
                    #     self.text_buffer += addable_part + "\n" if addable_part else ""
                    if self.udiff_line_start == "-":
                        self.removed_lines += 1
                    self.udiff_line_start = await self._get_udiff_line_start(self.diff_line_buffer.lstrip("\n\r"))
            self.udiff_line_start = await self._get_udiff_line_start(self.diff_line_buffer.lstrip("\n\r"))
        else:
            self.text_buffer += event.content.text

        if last_event and self.diff_line_buffer and self.udiff_line_start in [" ", "+"]:
            self.text_buffer += self.diff_line_buffer

        programming_language_block = re.search(r"<programming_language>(.*?)</programming_language>", self.text_buffer)
        file_path_block = re.search(r"<file_path>(.*?)</file_path>", self.text_buffer)
        is_diff_block = re.search(r"<is_diff>(.*?)</is_diff>", self.text_buffer)
        if programming_language_block and file_path_block and is_diff_block:
            self.is_diff = is_diff_block.group(1) == "true"
            self.event_buffer.append(
                CodeBlockStart(
                    content=CodeBlockStartContent(
                        language=programming_language_block.group(1),
                        filepath=file_path_block.group(1),
                        is_diff=self.is_diff,  # type: ignore
                    )
                )
            )

            if not self.is_diff:
                self.text_buffer = (
                    self.text_buffer.replace(programming_language_block.group(0), "")
                    .replace(file_path_block.group(0), "")
                    .replace(is_diff_block.group(0), "")
                ).lstrip("\n\r")
            else:
                diff_part = (
                    self.text_buffer.replace(programming_language_block.group(0), "")
                    .replace(file_path_block.group(0), "")
                    .replace(is_diff_block.group(0), "")
                )
                self.diff_line_buffer = diff_part
                self.diff_buffer = diff_part
                self.text_buffer = ""
            self.start_event_completed = True

        if self.start_event_completed and self.text_buffer:
            if self.first_data_block_sent:
                self.event_buffer.append(CodeBlockDelta(content=CodeBlockDeltaContent(code_delta=self.text_buffer)))
            else:
                self.first_data_block_sent = True
                self.event_buffer.append(
                    CodeBlockDelta(content=CodeBlockDeltaContent(code_delta=self.text_buffer.lstrip("\n\r")))
                )
            self.text_buffer = ""

        if last_event:
            if self.diff_buffer:
                self.event_buffer.append(
                    CodeBlockEnd(
                        content=CodeBlockEndContent(
                            diff=self.diff_buffer, added_lines=self.added_lines, removed_lines=self.removed_lines
                        )
                    )
                )
                self.diff_buffer = ""
            else:
                self.event_buffer.append(CodeBlockEnd(content=CodeBlockEndContent()))

        values_to_return = self.event_buffer
        self.event_buffer = []
        return values_to_return

    async def cleanup(self) -> None:
        await super().cleanup()
        self.diff_buffer = ""
        self.udiff_line_start = None
        self.is_diff = None
        self.added_lines = 0
        self.removed_lines = 0
        self.first_data_block_sent = False
        self.diff_line_buffer = ""


class Claude3Point5CodeQuerySolverPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
        You are an AI assistant helping a software engineer implement pull requests,
        and you have access to tools to interact with the engineer's codebase.
                
        Guidelines:
        - You are working in a codebase with other engineers and many different components. Be careful that changes you make in one component don't break other components.
        - When designing changes, implement them as a senior software engineer would. This means following best practices such as separating concerns and avoiding leaky interfaces.
        - When possible, choose the simpler solution.
        - Use your bash tool to set up any necessary environment variables, such as those needed to run tests.
        - You should run relevant tests to verify that your changes work.
        """

        focus_chunks_message = ""
        if self.params.get("focus_items"):
            focus_chunks_message = "The user has asked to focus on the following\n"
            for focus_item in self.params["focus_items"]:
                focus_chunks_message += (
                    "<item>"
                    + f"<type>{focus_item.type.value}</type>"
                    + (f"<value>{focus_item.value}</value>" if focus_item.value else "")
                    + (f"<path>{focus_item.path}</path>" if focus_item.type == FocusItemTypes.DIRECTORY else "")
                    + "\n".join([chunk.get_xml() for chunk in focus_item.chunks])
                    + "</item>"
                )

        user_message = f"""
            User Query: {self.params.get("query")}

            If you are thinking something, please provide that in <thinking> tag.
        """

        return UserAndSystemMessages(
            user_message=user_message if not focus_chunks_message else focus_chunks_message + user_message,
            system_message=system_message,
        )

    @classmethod
    def get_parsed_response_blocks(
        cls, response_block: List[MessageData]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []
        tool_use_map: Dict[str, Any] = {}
        for block in response_block:
            if isinstance(block, TextBlockData):
                final_content.extend(cls._get_parsed_custom_blocks(block.content.text))
            elif isinstance(block, ToolUseRequestData):
                tool_use_request_block = {
                    "type": "TOOL_USE_REQUEST_BLOCK",
                    "content": {
                        "tool_name": block.content.tool_name,
                        "tool_use_id": block.content.tool_use_id,
                        "tool_input_json": block.content.tool_input,
                    },
                }
                final_content.append(tool_use_request_block)
                tool_use_map[block.content.tool_use_id] = tool_use_request_block

        return final_content, tool_use_map

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:

        final_content: List[Dict[str, Any]] = []

        final_content = cls.get_parsed_response_blocks(llm_response.content)

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        return cls.parse_streaming_text_block_events(
            events=llm_response.content, parsers=[ThinkingParser(), CodeBlockParser(), SummaryParser()]
        )

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []

        # Define the patterns
        thinking_pattern = r"<thinking>(.*?)</thinking>"
        code_block_pattern = r"<code_block>(.*?)</code_block>"
        summary_pattern = r"<summary>(.*?)</summary>"

        # edge case, check if there is <code_block> tag in the input_string, and if it is not inside any other tag, and there
        # is not ending tag for it, then we append the ending tag for it
        # this is very rare, but can happen if the last block is not closed properly
        last_code_block_tag = input_string.rfind("<code_block>")
        if last_code_block_tag != -1 and input_string[last_code_block_tag:].rfind("</code_block>") == -1:
            input_string += "</code_block>"

        last_summary_tag = input_string.rfind("<summary>")
        if last_summary_tag != -1 and input_string[last_summary_tag:].rfind("</summary>") == -1:
            input_string += "</summary>"

        # for thinking tag, if there is no ending tag, then we just remove the tag, because we can show the thinking block without it
        last_thinking_tag = input_string.rfind("<thinking>")
        if last_thinking_tag != -1 and input_string[last_thinking_tag:].rfind("</thinking>") == -1:
            # remove the last thinking tag
            input_string = input_string[:last_thinking_tag] + input_string[last_thinking_tag + len("<thinking>") :]

        # Find all occurrences of either pattern
        matches_thinking = re.finditer(thinking_pattern, input_string, re.DOTALL)
        matches_code_block = re.finditer(code_block_pattern, input_string, re.DOTALL)
        matches_summary = re.finditer(summary_pattern, input_string, re.DOTALL)

        # Combine matches and sort by start position
        matches = list(matches_thinking) + list(matches_code_block) + list(matches_summary)
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
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:

        # Define the patterns
        language_pattern = r"<programming_language>(.*?)</programming_language>"
        file_path_pattern = r"<file_path>(.*?)</file_path>"
        is_diff_pattern = r"<is_diff>(.*?)</is_diff>"

        # Extract language and file path
        language_match = re.search(language_pattern, code_block_string)
        file_path_match = re.search(file_path_pattern, code_block_string)
        is_diff_match = re.search(is_diff_pattern, code_block_string)

        is_diff = is_diff_match.group(1).strip() == "true"

        language = language_match.group(1) if language_match else ""
        file_path = file_path_match.group(1) if file_path_match else ""

        # Extract code
        code = (
            code_block_string.replace(language_match.group(0), "")
            .replace(file_path_match.group(0), "")
            .replace(is_diff_match.group(0), "")
            .lstrip("\n\r")
        )

        diff = ""
        added_lines = 0
        removed_lines = 0

        if is_diff:
            code_selected_lines: List[str] = []
            code_lines = code.split("\n")

            for line in code_lines:
                if line.startswith(" ") or line.startswith("+") and not line.startswith("++"):
                    code_selected_lines.append(line[1:])
                if line.startswith("+"):
                    added_lines += 1
                elif line.startswith("-"):
                    removed_lines += 1

            code = "\n".join(code_selected_lines)
            diff = "\n".join(code_lines)

        return (
            {"language": language, "file_path": file_path, "code": code, "is_diff": is_diff}
            if not is_diff
            else {
                "language": language,
                "file_path": file_path,
                "code": code,
                "diff": diff,
                "is_diff": is_diff,
                "added_lines": added_lines,
                "removed_lines": removed_lines,
            }
        )
