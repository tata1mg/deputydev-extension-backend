import re
from typing import List, Optional, Tuple

from pydantic import BaseModel

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockDeltaContent,
    CodeBlockEnd,
    CodeBlockEndContent,
    CodeBlockStart,
    CodeBlockStartContent,
)
from deputydev_core.llm_handler.dataclasses.main import TextBlockDelta
from deputydev_core.llm_handler.providers.google.prompts.parsers.event_based.text_block_xml_parser import (
    BaseGoogleTextDeltaParser,
)


class CodeBlockParser(BaseGoogleTextDeltaParser):
    def __init__(self) -> None:
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

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:  # noqa: C901
        event.content.text = event.content.text.replace("```diff", "").replace("```", "")
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
                    if self.udiff_line_start == "-":
                        self.removed_lines += 1
                    self.udiff_line_start = await self._get_udiff_line_start(self.diff_line_buffer.lstrip("\n\r"))
            self.udiff_line_start = await self._get_udiff_line_start(
                self.diff_line_buffer.replace("```", "").lstrip("\n\r")
            )
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
