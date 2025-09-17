import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

ITERATIVE_FILE_READER = ConversationTool(
    name="iterative_file_reader",
    description=textwrap.dedent("""
        A built-in tool for reading file contents, either fully or by specified line ranges (1-indexed).
                                
        **Capabilities:**
        - Reads an entire file or a specific section between `start_line` and `end_line`.
        - For small files (≤ 1000 lines), full content is returned when no line range is provided.
        - For large files (> 1000 lines), a high-level summary is returned by default, including key constructs (e.g., classes, functions) and their line numbers.
        - When reading by range, the recommended maximum is 250 lines per call. Reading >1000 lines in a single request will result in an error.
        - Can be invoked iteratively to explore a file in parts until desired content is found.
                                
        **Notes:**
        - IMPORTANT: This tool is for files only; do not use it on directories.
        - Responses explicitly state whether the end of the file has been reached and whether the content is a summary or raw snippet.                         
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "file_path": JSONSchema(
                type="string", description="The full path to the file, relative to the root of the repository."
            ),
            "repo_path": JSONSchema(
                type="string",
                description="The absolute path to the root of the repository.",
            ),
            "start_line": JSONSchema(
                type="number",
                description="Optional. Start line to read from. It is 1 indexed. If not provided, it will read from the start of the file.",
            ),
            "end_line": JSONSchema(
                type="number",
                description="Optional. End line to read until. It is 1 indexed. If not provided, it will read until the end of the file.",
            ),
        },
        required=["file_path", "repo_path"],
        additionalProperties=False,
    ),
)
