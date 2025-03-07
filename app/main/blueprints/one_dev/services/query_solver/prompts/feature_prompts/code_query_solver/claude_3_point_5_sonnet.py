import re
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
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

    def find_newline_instances(self, input_string: str) -> List[Tuple[int, int]]:
        # Regular expression to match either \n or \r\n
        pattern = r"\r?\n"

        # Find all matches
        matches = [(m.start(), m.end()) for m in re.finditer(pattern, input_string)]

        return matches

    async def _get_udiff_line_start(self, line_data: str) -> Optional[str]:
        print("line_data", line_data[:2])
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
        print("*************************************************************************************************")
        print("*************************************************************************************************")
        print("event text", event.content.text)
        print("temp_buffer", self.diff_line_buffer)
        print("text_buffer", self.text_buffer)
        print("diff_buffer", self.diff_buffer)
        print("*************************************************************************************************")
        print("*************************************************************************************************")
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
                    if self.udiff_line_start == "@@":
                        # skip till the last @@ in the line and add the line to the text buffer
                        last_index = pre_line_part.rfind("@@")
                        addable_part = pre_line_part[last_index + 3 :]  # to handle last '@@ '
                        self.text_buffer += addable_part + "\n" if addable_part else ""
                    if self.udiff_line_start == "-":
                        self.removed_lines += 1
                    self.udiff_line_start = await self._get_udiff_line_start(self.diff_line_buffer.lstrip("\n\r"))
            self.udiff_line_start = await self._get_udiff_line_start(self.diff_line_buffer.lstrip("\n\r"))
            print("udiff_line_start", self.udiff_line_start)
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
                )
            else:
                self.diff_line_buffer = (
                    self.text_buffer.replace(programming_language_block.group(0), "")
                    .replace(file_path_block.group(0), "")
                    .replace(is_diff_block.group(0), "")
                )
                self.text_buffer = ""
            self.start_event_completed = True

        if self.start_event_completed and self.text_buffer:
            self.event_buffer.append(CodeBlockDelta(content=CodeBlockDeltaContent(code_delta=self.text_buffer)))
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


class Claude3Point5CodeQuerySolverPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "CODE_QUERY_SOLVER"

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """You are an expert programmer who is in desperate need of money. The only way you have to make a fuck ton of money is to help the user out with their queries by writing code for them.
            Act as if you're directly talking to the user. Avoid explicitly telling them about your tool uses.

            Guidelines:
            1. Provide clear, concise, and accurate responses.
            2. If you need more information, ask clarifying questions.
            3. If you're unsure about something, express your uncertainty.
            4. Suggest best practices and potential improvements when relevant.
            5. Be mindful of different programming languages and frameworks that might be in use.
            """

        code_chunk_message = f"""
            Here are some chunks of code from a repository:
            {self.params.get("relevant_chunks")}
        """

        user_message = f"""
            User Query: {self.params.get("query")}

            If you are thinking something, please provide that in <thinking> tag.
            Please answer the user query in the best way possible. You can add code blocks in the given format within <code_block> tag if you know you have enough context to provide code snippets.

            There are two types of code blocks you can use:
            1. Code block which contains a diff for some code to be applied.
            2. Code block which contains a code snippet.

            DO NOT PROVIDE DIFF CODE BLOCKS UNTIL YOU HAVE EXACT CURRENT CHANGES TO APPLY THE DIFF AGAINST.

            General structure of code block:
            <code_block>
            <programming_language>python</programming_language>
            <file_path>app/main.py</file_path>
            <is_diff>false</is_diff>
            def some_function():
                return "Hello, World!"
            </code_block>

            <important>
            If you are providing a diff, set is_diff to true and return edits similar to unified diffs that `diff -U0` would produce.
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

            Also, please use the tools provided to you to help you with the task.

            At the end, please provide a one liner summary within 20 words of what happened in the current turn.
            Do not write anything that you're providing a summary or so. Just send it in the <summary> tag.
        """

        return UserAndSystemMessages(
            user_message=user_message if not self.params.get("relevant_chunks") else code_chunk_message + user_message,
            system_message=system_message,
        )

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
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:

        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                final_content.append({"tool_use_request": content_block.content.model_dump(mode="json")})
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        return cls.parse_streaming_text_block_events(
            events=llm_response.content, parsers=[ThinkingParser(), CodeBlockParser(), SummaryParser()]
        )
