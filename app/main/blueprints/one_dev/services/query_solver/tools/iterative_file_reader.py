import textwrap

from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

ITERATIVE_FILE_READER = ConversationTool(
    name="iterative_file_reader",
    description=textwrap.dedent("""
        This is a built-in tool.

        Reads content of a file, and optionally between a specific range of lines if a start line and/or end line is provided. (1 indexed).

        If the file is small (<=1000 lines) and the entire file is requested, it will return the full content.
        If the file is large (>1000 lines) and the entire file is requested, it will return a summary instead of the full content. The summary will contain an overview of the file's constructs (classes, functions, etc.) and their line numbers.

        If summary content is returned, the tool can be run again with specific start and end lines to read more detailed content.

        This tool can be used iteratively, to read a file until either the desired context is found.
        If using this tool iteratively, the `start_line` and `end_line` parameters should be used to specify the range of lines to read in each iteration. The recommended maximum range is 500 lines, but it can be adjusted based on the file size and content.
        A range of greater than 1000 lines, when provided explicitly, will automatically trigger an error.

        The response will EXPLICITLY mention if the end of the file is reached or not.
    """),
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The complete path of the file relative to the repo root",
                },
                "start_line": {
                    "type": "number",
                    "description": "Optional. Start line to read from. It is 1 indexed. If not provided, it will read from the start of the file.",
                },
                "end_line": {
                    "type": "number",
                    "description": "Optional. End line to read until. It is 1 indexed. If not provided, it will read until the end of the file.",
                },
            },
            "required": ["file_path"],
            "additionalProperties": False,
        }
    ),
)
