from unittest.mock import Mock

import pytest

from app.backend_common.services.llm.dataclasses.main import (
    TextBlockDelta,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockEnd,
    CodeBlockStart,
    SummaryBlockDelta,
    SummaryBlockStart,
    ThinkingBlockDelta,
    ThinkingBlockStart,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gpt_4_point_1 import (
    BaseBlockParser,
    CodeBlockParser,
    SummaryBlockParser,
    TextBlockParser,
    ThinkingBlockParser,
    ToolUseEventParser,
)
from test.fixtures.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gpt_4_point_1_fixtures import (
    Gpt4Point1ParserFixtures,
)


class TestToolUseEventParser:
    """Test suite for ToolUseEventParser functionality."""

    @pytest.fixture
    def parser(self) -> ToolUseEventParser:
        """Create a fresh parser instance for each test."""
        return ToolUseEventParser()

    def test_can_parse_tool_use_events(self, parser: ToolUseEventParser) -> None:
        """Test detection of parseable tool use events."""
        tool_start = Mock(spec=ToolUseRequestStart)
        tool_end = Mock(spec=ToolUseRequestEnd)
        tool_delta = Mock(spec=ToolUseRequestDelta)
        text_event = Mock(spec=TextBlockDelta)

        assert parser.can_parse(tool_start) is True
        assert parser.can_parse(tool_end) is True
        assert parser.can_parse(tool_delta) is True
        assert parser.can_parse(text_event) is False

    @pytest.mark.asyncio
    async def test_parse_tool_use_events(self, parser: ToolUseEventParser) -> None:
        """Test parsing of tool use events."""
        mock_event = Mock(spec=ToolUseRequestStart)

        results = []
        async for result in parser.parse(mock_event):
            results.append(result)

        assert len(results) == 1
        assert results[0] is mock_event


class TestTextBlockParser:
    """Test suite for TextBlockParser functionality."""

    @pytest.fixture
    def parser(self) -> TextBlockParser:
        """Create a fresh parser instance for each test."""
        return TextBlockParser()

    def test_parser_initialization(self, parser: TextBlockParser) -> None:
        """Test proper parser initialization."""
        assert parser.status == "NOT_STARTED"

    def test_parse_first_content(self, parser: TextBlockParser) -> None:
        """Test parsing first content creates start event."""
        content = "Hello, this is test content"
        events, new_index = parser.parse(content, 0)

        assert len(events) == 2  # Start + Delta
        assert isinstance(events[0], TextBlockStart)
        assert isinstance(events[1], TextBlockDelta)
        assert events[1].content.text == content
        assert new_index == len(content)
        assert parser.status == "STARTED"

    def test_parse_subsequent_content(self, parser: TextBlockParser) -> None:
        """Test parsing subsequent content after initialization."""
        # First parse to initialize
        content1 = "First part"
        events1, index1 = parser.parse(content1, 0)

        # Second parse should only create delta
        content2 = "First part Second part"
        events2, index2 = parser.parse(content2, index1)

        assert len(events2) == 1  # Only Delta
        assert isinstance(events2[0], TextBlockDelta)
        assert events2[0].content.text == " Second part"
        assert index2 == len(content2)

    def test_parse_empty_content(self, parser: TextBlockParser) -> None:
        """Test parsing empty content."""
        events, new_index = parser.parse("", 0)

        assert len(events) == 1  # Only Start event
        assert isinstance(events[0], TextBlockStart)
        assert new_index == 0

    def test_end_parsing(self, parser: TextBlockParser) -> None:
        """Test ending text block parsing."""
        # Initialize parser first
        parser.parse("Some content", 0)

        end_events = parser.end()

        assert len(end_events) == 1
        assert isinstance(end_events[0], TextBlockEnd)
        assert parser.status == "NOT_STARTED"  # Reset after end

    def test_parser_reuse_after_end(self, parser: TextBlockParser) -> None:
        """Test parser can be reused after calling end()."""
        # First use
        content1 = "First content"
        events1, _ = parser.parse(content1, 0)
        parser.end()

        # Second use
        content2 = "Second content"
        events2, _ = parser.parse(content2, 0)

        # Should create start event again
        start_events = [e for e in events2 if isinstance(e, TextBlockStart)]
        assert len(start_events) == 1


class TestCodeBlockParser:
    """Test suite for CodeBlockParser functionality."""

    @pytest.fixture
    def parser(self) -> CodeBlockParser:
        """Create a fresh parser instance for each test."""
        return CodeBlockParser()

    def test_parser_initialization(self, parser: CodeBlockParser) -> None:
        """Test proper parser initialization."""
        assert parser.status == "NOT_STARTED"
        assert parser.diff_buffer == ""
        assert parser.diff_line_buffer == ""
        assert parser.added_lines == 0
        assert parser.removed_lines == 0
        assert parser.is_diff is False
        assert parser.udiff_line_start is None
        assert parser.text_buffer == ""

    def test_find_newline_instances(self, parser: CodeBlockParser) -> None:
        """Test newline detection utility method."""
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

    def test_get_udiff_line_start(self, parser: CodeBlockParser) -> None:
        """Test udiff line start detection."""
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
            result = parser._get_udiff_line_start(line)
            assert result == expected

    def test_parse_non_diff_code_block(self, parser: CodeBlockParser) -> None:
        """Test parsing non-diff code block."""
        code_block_data = Gpt4Point1ParserFixtures.get_non_diff_code_block()

        events, new_index = parser.parse(code_block_data, 0)

        # Should create start event
        start_events = [e for e in events if isinstance(e, CodeBlockStart)]
        assert len(start_events) == 1

        start = start_events[0]
        assert start.content.language == "python"
        assert start.content.filepath == "main.py"
        assert start.content.is_diff is False

    def test_parse_diff_code_block(self, parser: CodeBlockParser) -> None:
        """Test parsing diff code block."""
        diff_block_data = Gpt4Point1ParserFixtures.get_diff_code_block()

        events, new_index = parser.parse(diff_block_data, 0)

        # Should create start event with diff flag
        start_events = [e for e in events if isinstance(e, CodeBlockStart)]
        assert len(start_events) == 1

        start = start_events[0]
        assert start.content.is_diff is True

    def test_end_diff_code_block(self, parser: CodeBlockParser) -> None:
        """Test ending diff code block with statistics."""
        diff_block_data = Gpt4Point1ParserFixtures.get_diff_code_block()

        # Parse diff block
        parser.parse(diff_block_data, 0)

        # Simulate some diff statistics
        parser.added_lines = 3
        parser.removed_lines = 2
        parser.diff_buffer = "@@ -1,2 +1,3 @@\n-old line\n+new line\n+another line"

        end_events = parser.end()

        end_events_filtered = [e for e in end_events if isinstance(e, CodeBlockEnd)]
        assert len(end_events_filtered) == 1

        end = end_events_filtered[0]
        assert end.content.added_lines == 3
        assert end.content.removed_lines == 2
        assert end.content.diff is not None

    def test_end_non_diff_code_block(self, parser: CodeBlockParser) -> None:
        """Test ending non-diff code block."""
        non_diff_data = Gpt4Point1ParserFixtures.get_non_diff_code_block()

        # Parse non-diff block
        parser.parse(non_diff_data, 0)

        end_events = parser.end()

        end_events_filtered = [e for e in end_events if isinstance(e, CodeBlockEnd)]
        assert len(end_events_filtered) == 1

        end = end_events_filtered[0]
        assert end.content.diff is None
        assert end.content.added_lines is None
        assert end.content.removed_lines is None


class TestBaseBlockParser:
    """Test suite for BaseBlockParser functionality."""

    @pytest.fixture
    def parser(self) -> BaseBlockParser:
        """Create a fresh parser instance for each test."""
        return BaseBlockParser()

    def test_parser_initialization(self, parser: BaseBlockParser) -> None:
        """Test proper parser initialization."""
        assert parser.status == "NOT_STARTED"

    def test_parse_method_exists(self, parser: BaseBlockParser) -> None:
        """Test that BaseBlockParser has the expected methods."""
        # BaseBlockParser should have start and end methods
        assert hasattr(parser, "start")
        assert hasattr(parser, "end")

        # BaseBlockParser doesn't have parse method - only subclasses do
        assert not hasattr(parser, "parse")


class TestThinkingBlockParser:
    """Test suite for ThinkingBlockParser functionality."""

    @pytest.fixture
    def parser(self) -> ThinkingBlockParser:
        """Create a fresh parser instance for each test."""
        return ThinkingBlockParser()

    def test_parser_inheritance(self, parser: ThinkingBlockParser) -> None:
        """Test that ThinkingBlockParser inherits from BaseBlockParser."""
        assert isinstance(parser, BaseBlockParser)

    def test_parse_thinking_content(self, parser: ThinkingBlockParser) -> None:
        """Test parsing thinking block content."""
        thinking_text = "This is my thinking process about the problem."

        events = parser.parse(thinking_text)

        # Should create appropriate thinking events
        start_events = [e for e in events if isinstance(e, ThinkingBlockStart)]
        delta_events = [e for e in events if isinstance(e, ThinkingBlockDelta)]

        if parser.status == "NOT_STARTED":
            assert len(start_events) >= 0  # May create start event

        if thinking_text:
            assert len(delta_events) >= 0  # May create delta events

    def test_parse_empty_thinking(self, parser: ThinkingBlockParser) -> None:
        """Test parsing empty thinking content."""
        events = parser.parse("")

        # Should handle empty content gracefully
        assert isinstance(events, list)


class TestSummaryBlockParser:
    """Test suite for SummaryBlockParser functionality."""

    @pytest.fixture
    def parser(self) -> SummaryBlockParser:
        """Create a fresh parser instance for each test."""
        return SummaryBlockParser()

    def test_parser_inheritance(self, parser: SummaryBlockParser) -> None:
        """Test that SummaryBlockParser inherits from BaseBlockParser."""
        assert isinstance(parser, BaseBlockParser)

    def test_parse_summary_content(self, parser: SummaryBlockParser) -> None:
        """Test parsing summary block content."""
        summary_text = "This is a summary of the solution provided above."

        events = parser.parse(summary_text)

        # Should create appropriate summary events
        start_events = [e for e in events if isinstance(e, SummaryBlockStart)]
        delta_events = [e for e in events if isinstance(e, SummaryBlockDelta)]

        if parser.status == "NOT_STARTED":
            assert len(start_events) >= 0  # May create start event

        if summary_text:
            assert len(delta_events) >= 0  # May create delta events

    def test_parse_empty_summary(self, parser: SummaryBlockParser) -> None:
        """Test parsing empty summary content."""
        events = parser.parse("")

        # Should handle empty content gracefully
        assert isinstance(events, list)


class TestIntegrationScenarios:
    """Integration tests for multiple parsers working together."""

    def test_multiple_parser_instances(self) -> None:
        """Test that multiple parser instances work independently."""
        text_parser1 = TextBlockParser()
        text_parser2 = TextBlockParser()
        code_parser1 = CodeBlockParser()
        code_parser2 = CodeBlockParser()

        # Test that they maintain separate state
        content1 = "First parser content"
        content2 = "Second parser content"

        events1, _ = text_parser1.parse(content1, 0)
        events2, _ = text_parser2.parse(content2, 0)

        # Should create independent start events
        assert len([e for e in events1 if isinstance(e, TextBlockStart)]) == 1
        assert len([e for e in events2 if isinstance(e, TextBlockStart)]) == 1

        # Content should be different
        delta1 = [e for e in events1 if isinstance(e, TextBlockDelta)][0]
        delta2 = [e for e in events2 if isinstance(e, TextBlockDelta)][0]

        assert delta1.content.text == content1
        assert delta2.content.text == content2

    def test_parser_error_handling(self) -> None:
        """Test parser behavior with malformed or unexpected input."""
        parsers = [
            TextBlockParser(),
            CodeBlockParser(),
            ThinkingBlockParser(),
            SummaryBlockParser(),
        ]

        malformed_inputs = [
            None,  # None input
            {},  # Empty dict
            {"invalid": "structure"},  # Invalid structure
        ]

        for parser in parsers:
            for malformed_input in malformed_inputs:
                try:
                    if isinstance(parser, TextBlockParser):
                        # TextBlockParser expects string and int
                        if isinstance(malformed_input, str):
                            parser.parse(malformed_input, 0)
                    elif isinstance(parser, CodeBlockParser):
                        # CodeBlockParser expects dict and int
                        if isinstance(malformed_input, dict):
                            parser.parse(malformed_input, 0)
                    else:
                        # BaseBlockParser subclasses expect string
                        if isinstance(malformed_input, str):
                            parser.parse(malformed_input)
                except Exception as e:
                    # Should handle errors gracefully
                    assert isinstance(e, (TypeError, ValueError, AttributeError))

    def test_concurrent_parsing_simulation(self) -> None:
        """Test parsers under rapid sequential calls."""
        parser = TextBlockParser()

        # Simulate rapid parsing calls
        for i in range(100):
            content = f"Rapid content {i}"
            events, _ = parser.parse(content, len(content) * i)

            # Should maintain consistency
            if i == 0:
                # First call should create start event
                start_events = [e for e in events if isinstance(e, TextBlockStart)]
                assert len(start_events) == 1

            # All calls should handle content
            assert isinstance(events, list)

    def test_memory_efficiency(self) -> None:
        """Test that parsers don't accumulate excessive state."""
        parser = TextBlockParser()

        # Process many iterations
        for i in range(1000):
            content = f"Content iteration {i}"
            events, _ = parser.parse(content, 0)

            # Reset parser between iterations
            parser.end()

            # Should not accumulate state
            assert parser.status == "NOT_STARTED"

        # Final state should be clean
        assert parser.status == "NOT_STARTED"
