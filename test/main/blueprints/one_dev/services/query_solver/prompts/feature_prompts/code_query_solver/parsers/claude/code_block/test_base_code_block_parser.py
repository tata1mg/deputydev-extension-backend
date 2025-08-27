import pytest

from app.backend_common.services.llm.dataclasses.main import TextBlockDelta, TextBlockDeltaContent
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockEnd,
    CodeBlockStart,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.claude.code_block.base_code_block_parser import (
    CodeBlockParser,
)


class TestCodeBlockParser:
    """Test suite for CodeBlockParser functionality."""

    @pytest.fixture
    def parser(self) -> CodeBlockParser:
        """Create a fresh parser instance for each test."""
        return CodeBlockParser()

    @pytest.fixture
    def sample_header(self) -> str:
        """Sample code block header for testing."""
        return (
            "<programming_language>python</programming_language>"
            "<file_path>src/example.py</file_path>"
            "<is_diff>false</is_diff>"
        )

    @pytest.fixture
    def sample_diff_header(self) -> str:
        """Sample diff code block header for testing."""
        return (
            "<programming_language>javascript</programming_language>"
            "<file_path>src/components/Button.jsx</file_path>"
            "<is_diff>true</is_diff>"
        )

    def create_text_delta(self, text: str) -> TextBlockDelta:
        """Helper method to create TextBlockDelta objects."""
        return TextBlockDelta(content=TextBlockDeltaContent(text=text))

    # ===============================
    # NON-DIFF CODE BLOCK TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_parse_simple_non_diff_code_block(self, parser: CodeBlockParser) -> None:
        """Test parsing a simple non-diff code block in a single event."""
        text = (
            "<programming_language>python</programming_language>"
            "<file_path>main.py</file_path>"
            "<is_diff>false</is_diff>\n"
            "print('hello world')"
        )

        event = self.create_text_delta(text)
        results = await parser.parse_text_delta(event, last_event=True)

        # Verify the structure and content
        assert len(results) == 3

        # Check CodeBlockStart
        start_block = results[0]
        assert isinstance(start_block, CodeBlockStart)
        assert start_block.content.language == "python"
        assert start_block.content.filepath == "main.py"
        assert start_block.content.is_diff is False

        # Check CodeBlockDelta
        delta_block = results[1]
        assert isinstance(delta_block, CodeBlockDelta)
        assert "print('hello world')" in delta_block.content.code_delta

        # Check CodeBlockEnd
        end_block = results[2]
        assert isinstance(end_block, CodeBlockEnd)
        assert end_block.content.diff is None
        assert end_block.content.added_lines is None
        assert end_block.content.removed_lines is None

    @pytest.mark.asyncio
    async def test_parse_multi_line_non_diff_code_block(self, parser: CodeBlockParser) -> None:
        """Test parsing a multi-line non-diff code block."""
        header = (
            "<programming_language>python</programming_language>"
            "<file_path>utils/helper.py</file_path>"
            "<is_diff>false</is_diff>\n"
        )

        code_lines = [
            "def calculate_sum(a, b):\n",
            '    """Calculate sum of two numbers."""\n',
            "    return a + b\n",
            "\n",
            "if __name__ == '__main__':\n",
            "    result = calculate_sum(5, 3)\n",
            "    print(f'Result: {result}')",
        ]

        # Parse header first
        header_event = self.create_text_delta(header)
        results = await parser.parse_text_delta(header_event)

        assert len(results) == 1
        assert isinstance(results[0], CodeBlockStart)
        assert results[0].content.language == "python"
        assert results[0].content.is_diff is False

        # Parse code lines
        all_deltas = []
        for line in code_lines[:-1]:  # All but last
            code_event = self.create_text_delta(line)
            results = await parser.parse_text_delta(code_event)
            if results:
                all_deltas.extend([r for r in results if isinstance(r, CodeBlockDelta)])

        # Parse last line with last_event=True
        last_event = self.create_text_delta(code_lines[-1])
        results = await parser.parse_text_delta(last_event, last_event=True)

        # Verify we have deltas and an end block
        deltas = [r for r in results if isinstance(r, CodeBlockDelta)]
        end_blocks = [r for r in results if isinstance(r, CodeBlockEnd)]

        assert len(deltas) >= 1
        assert len(end_blocks) == 1

        # Verify content is preserved
        all_delta_content = "".join(delta.content.code_delta for delta in all_deltas + deltas)
        expected_content = "".join(code_lines)
        assert all_delta_content.strip() == expected_content.strip()

    @pytest.mark.asyncio
    async def test_parse_non_diff_with_different_languages(self, parser: CodeBlockParser) -> None:
        """Test parsing code blocks with different programming languages."""
        test_cases = [
            ("javascript", "const x = 42;"),
            ("typescript", "interface User { name: string; }"),
            ("java", "public class Main { }"),
            ("rust", 'fn main() { println!("Hello!"); }'),
            ("go", 'package main\nimport "fmt"'),
        ]

        for language, code in test_cases:
            text = (
                f"<programming_language>{language}</programming_language>"
                f"<file_path>test.{language}</file_path>"
                "<is_diff>false</is_diff>\n"
                f"{code}"
            )

            event = self.create_text_delta(text)
            results = await parser.parse_text_delta(event, last_event=True)

            assert len(results) >= 2  # At least start and end
            start_block = results[0]
            assert isinstance(start_block, CodeBlockStart)
            assert start_block.content.language == language
            assert start_block.content.is_diff is False

            # Reset parser for next iteration
            await parser.cleanup()

    # ===============================
    # DIFF CODE BLOCK TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_parse_simple_diff_code_block(self, parser: CodeBlockParser) -> None:
        """Test parsing a simple diff code block."""
        # Header with metadata
        header = (
            "<programming_language>python</programming_language><file_path>main.py</file_path><is_diff>true</is_diff>\n"
        )

        header_event = self.create_text_delta(header)
        results = await parser.parse_text_delta(header_event)

        assert len(results) == 1
        assert isinstance(results[0], CodeBlockStart)
        assert results[0].content.is_diff is True

        # Diff content
        diff_lines = [
            "@@ -1,2 +1,2 @@\n",
            "-print('hello')\n",
            "+print('hello world')\n",
        ]

        for line in diff_lines:
            event = self.create_text_delta(line)
            await parser.parse_text_delta(event)

        # Final flush
        results = await parser.parse_text_delta(self.create_text_delta(""), last_event=True)

        # Verify end block with diff stats
        end_blocks = [r for r in results if isinstance(r, CodeBlockEnd)]
        assert len(end_blocks) == 1

        end_block = end_blocks[0]
        assert end_block.content.diff is not None
        assert "@@" in end_block.content.diff
        assert end_block.content.added_lines == 1
        assert end_block.content.removed_lines == 1

    @pytest.mark.asyncio
    async def test_parse_complex_diff_with_multiple_hunks(self, parser: CodeBlockParser) -> None:
        """Test parsing a complex diff with multiple hunks."""
        header = (
            "<programming_language>python</programming_language>"
            "<file_path>src/calculator.py</file_path>"
            "<is_diff>true</is_diff>\n"
        )

        header_event = self.create_text_delta(header)
        results = await parser.parse_text_delta(header_event)
        assert len(results) == 1
        assert isinstance(results[0], CodeBlockStart)

        # Complex diff with multiple hunks
        diff_content = [
            "@@ -1,5 +1,6 @@\n",
            " def add(a, b):\n",
            "-    return a + b\n",
            '+    """Add two numbers."""\n',
            "+    return a + b\n",
            " \n",
            " def subtract(a, b):\n",
            "@@ -10,3 +11,4 @@\n",
            " def multiply(a, b):\n",
            "-    return a * b\n",
            '+    """Multiply two numbers."""\n',
            "+    return a * b\n",
        ]

        for line in diff_content:
            event = self.create_text_delta(line)
            await parser.parse_text_delta(event)

        # Final flush
        results = await parser.parse_text_delta(self.create_text_delta(""), last_event=True)

        end_blocks = [r for r in results if isinstance(r, CodeBlockEnd)]
        assert len(end_blocks) == 1

        end_block = end_blocks[0]
        assert end_block.content.diff is not None
        assert end_block.content.added_lines == 4  # 4 lines added
        assert end_block.content.removed_lines == 2  # 2 lines removed

    @pytest.mark.asyncio
    async def test_diff_line_counting_accuracy(self, parser: CodeBlockParser) -> None:
        """Test accurate counting of added and removed lines in diffs."""
        header = (
            "<programming_language>python</programming_language><file_path>test.py</file_path><is_diff>true</is_diff>\n"
        )

        header_event = self.create_text_delta(header)
        await parser.parse_text_delta(header_event)

        # Diff with specific additions and deletions
        diff_lines = [
            "@@ -1,8 +1,10 @@\n",
            " import os\n",
            "-import sys\n",  # 1 removal
            "+import sys\n",  # 1 addition
            "+import json\n",  # 1 addition
            "+import time\n",  # 1 addition
            " \n",
            " def main():\n",
            "-    print('old')\n",  # 1 removal
            "-    print('version')\n",  # 1 removal
            "+    print('new version')\n",  # 1 addition
            "     return 0\n",
        ]

        for line in diff_lines:
            event = self.create_text_delta(line)
            await parser.parse_text_delta(event)

        results = await parser.parse_text_delta(self.create_text_delta(""), last_event=True)

        end_blocks = [r for r in results if isinstance(r, CodeBlockEnd)]
        assert len(end_blocks) == 1

        end_block = end_blocks[0]
        assert end_block.content.added_lines == 4  # 4 additions
        assert end_block.content.removed_lines == 3  # 3 removals

    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================

    @pytest.mark.asyncio
    async def test_empty_code_block(self, parser: CodeBlockParser) -> None:
        """Test parsing an empty code block."""
        text = (
            "<programming_language>python</programming_language>"
            "<file_path>empty.py</file_path>"
            "<is_diff>false</is_diff>\n"
        )

        event = self.create_text_delta(text)
        results = await parser.parse_text_delta(event, last_event=True)

        assert len(results) >= 2  # At least start and end
        assert isinstance(results[0], CodeBlockStart)
        assert isinstance(results[-1], CodeBlockEnd)

    @pytest.mark.asyncio
    async def test_malformed_header_handling(self, parser: CodeBlockParser) -> None:
        """Test behavior with incomplete or malformed headers."""
        incomplete_header = (
            "<programming_language>python</programming_language><file_path>test.py</file_path>"
            # Missing is_diff tag
        )

        event = self.create_text_delta(incomplete_header)
        results = await parser.parse_text_delta(event, last_event=True)

        # Should not produce CodeBlockStart without complete header
        start_blocks = [r for r in results if isinstance(r, CodeBlockStart)]
        assert len(start_blocks) == 0

    @pytest.mark.asyncio
    async def test_special_characters_in_paths(self, parser: CodeBlockParser) -> None:
        """Test handling of special characters in file paths."""
        special_paths = [
            "src/components/Button-v2.tsx",
            "tests/unit/test_file_parser.py",
            "config/app.config.json",
            "docs/api/v1/endpoints.md",
            "scripts/build-and-deploy.sh",
        ]

        for path in special_paths:
            text = (
                "<programming_language>python</programming_language>"
                f"<file_path>{path}</file_path>"
                "<is_diff>false</is_diff>\n"
                "# Sample content"
            )

            event = self.create_text_delta(text)
            results = await parser.parse_text_delta(event, last_event=True)

            start_blocks = [r for r in results if isinstance(r, CodeBlockStart)]
            assert len(start_blocks) == 1
            assert start_blocks[0].content.filepath == path

            await parser.cleanup()

    @pytest.mark.asyncio
    async def test_whitespace_handling(self, parser: CodeBlockParser) -> None:
        """Test proper handling of various whitespace scenarios."""
        text_with_tabs = (
            "<programming_language>python</programming_language>"
            "<file_path>main.py</file_path>"
            "<is_diff>false</is_diff>\n"
            "\tdef func():\n"
            "\t\treturn True"
        )

        event = self.create_text_delta(text_with_tabs)
        results = await parser.parse_text_delta(event, last_event=True)

        delta_blocks = [r for r in results if isinstance(r, CodeBlockDelta)]
        assert len(delta_blocks) >= 1

        # Verify tabs are preserved
        combined_content = "".join(delta.content.code_delta for delta in delta_blocks)
        assert "\t" in combined_content

    # ===============================
    # STREAMING AND INCREMENTAL PARSING
    # ===============================

    @pytest.mark.asyncio
    async def test_incremental_parsing_large_content(self, parser: CodeBlockParser) -> None:
        """Test streaming parsing of large code content."""
        header = (
            "<programming_language>python</programming_language>"
            "<file_path>large_file.py</file_path>"
            "<is_diff>false</is_diff>\n"
        )

        # Parse header
        header_event = self.create_text_delta(header)
        results = await parser.parse_text_delta(header_event)
        assert len(results) == 1
        assert isinstance(results[0], CodeBlockStart)

        # Stream content in small chunks
        content_chunks = [
            "import os\n",
            "import sys\n",
            "from typing import List\n",
            "\n",
            "class DataProcessor:\n",
            "    def __init__(self):\n",
            "        self.data = []\n",
            "\n",
            "    def process(self, items: List[str]):\n",
            "        for item in items:\n",
            "            self.data.append(item.strip())\n",
            "        return self.data\n",
        ]

        all_deltas = []
        for chunk in content_chunks[:-1]:
            event = self.create_text_delta(chunk)
            results = await parser.parse_text_delta(event)
            deltas = [r for r in results if isinstance(r, CodeBlockDelta)]
            all_deltas.extend(deltas)

        # Final chunk
        final_event = self.create_text_delta(content_chunks[-1])
        results = await parser.parse_text_delta(final_event, last_event=True)

        final_deltas = [r for r in results if isinstance(r, CodeBlockDelta)]
        end_blocks = [r for r in results if isinstance(r, CodeBlockEnd)]

        all_deltas.extend(final_deltas)

        assert len(end_blocks) == 1
        assert len(all_deltas) >= 1

        # Verify all content is captured
        total_content = "".join(delta.content.code_delta for delta in all_deltas)
        expected_content = "".join(content_chunks)
        assert total_content.strip() == expected_content.strip()

    # ===============================
    # STATE MANAGEMENT TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_cleanup_resets_all_state(self, parser: CodeBlockParser) -> None:
        """Test that cleanup properly resets all parser state."""
        # Set up parser with some state
        parser.diff_buffer = "sample diff content"
        parser.added_lines = 5
        parser.removed_lines = 3
        parser.is_diff = True
        parser.text_buffer = "some text"
        parser.first_data_block_sent = True
        parser.diff_line_buffer = "diff line"
        parser.udiff_line_start = "+"

        await parser.cleanup()

        # Verify all state is reset
        assert parser.diff_buffer == ""
        assert parser.added_lines == 0
        assert parser.removed_lines == 0
        assert parser.is_diff is None
        assert parser.text_buffer == ""
        assert parser.first_data_block_sent is False
        assert parser.diff_line_buffer == ""
        assert parser.udiff_line_start is None
        assert parser.event_buffer == []
        assert parser.start_event_completed is False

    @pytest.mark.asyncio
    async def test_parser_reuse_after_cleanup(self, parser: CodeBlockParser) -> None:
        """Test that parser can be reused after cleanup."""
        # First parse
        text1 = (
            "<programming_language>python</programming_language>"
            "<file_path>file1.py</file_path>"
            "<is_diff>false</is_diff>\n"
            "print('first')"
        )

        event1 = self.create_text_delta(text1)
        results1 = await parser.parse_text_delta(event1, last_event=True)
        assert len(results1) >= 2

        # Cleanup
        await parser.cleanup()

        # Second parse with different content
        text2 = (
            "<programming_language>javascript</programming_language>"
            "<file_path>file2.js</file_path>"
            "<is_diff>false</is_diff>\n"
            "console.log('second');"
        )

        event2 = self.create_text_delta(text2)
        results2 = await parser.parse_text_delta(event2, last_event=True)

        assert len(results2) >= 2
        start_block = results2[0]
        assert isinstance(start_block, CodeBlockStart)
        assert start_block.content.language == "javascript"
        assert start_block.content.filepath == "file2.js"

    # ===============================
    # HELPER METHOD TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_find_newline_instances(self, parser: CodeBlockParser) -> None:
        """Test the newline finding utility method."""
        test_cases = [
            ("hello\nworld", [(5, 6)]),
            ("line1\r\nline2\nline3", [(5, 7), (12, 13)]),
            ("no newlines", []),
            ("\n\n\n", [(0, 1), (1, 2), (2, 3)]),
            ("", []),
        ]

        for text, expected in test_cases:
            result = parser.find_newline_instances(text)
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_udiff_line_start(self, parser: CodeBlockParser) -> None:
        """Test the udiff line start detection method."""
        test_cases = [
            ("@@ -1,2 +1,2 @@", "@@"),
            ("--- a/file.txt", "---"),
            ("+++ b/file.txt", "+++"),
            (" unchanged line", " "),
            ("+added line", "+"),
            ("-removed line", "-"),
            ("invalid line", None),
            ("", None),
        ]

        for line, expected in test_cases:
            result = await parser._get_udiff_line_start(line)
            assert result == expected
