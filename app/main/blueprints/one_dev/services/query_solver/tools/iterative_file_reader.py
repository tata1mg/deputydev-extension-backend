from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

ITERATIVE_FILE_READER = ConversationTool(
    name="iterative_file_reader",
    description="""
        This is a built-in tool.
        Reads content of a file from a given start line number (1 indexed) to an end line number (1 indexed).
        This tool can be used iteratively to read a file in chunks by just providing the offset line.
        At once, it can read maximum of 100 lines.
        If you do not know the end line number, just provide the end line number as start_line + 100.
        It will let you know if the end of the file is reached.
        To use this, a valid file path is required.

        Try to use this tool iteratively, to read a file until either the desired context is found or the end of the file is reached.
        The response will EXPLICITLY mention if the end of the file is reached or not.

        Special behavior for entire file requests:
        - If you request the entire file (start_line=1 and end_line covers the whole file) and the file has more than 1000 lines, you will receive a summary instead of the full content.
        - The summary will contain an overview of the file's constructs (classes, functions, etc.) and their sizes/line counts.
        - For files with 1000 lines or fewer, you will receive the complete file content as usual.
    """,
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
                    "description": "Start line to read from. It is 1 indexed.",
                },
                "end_line": {
                    "type": "number",
                    "description": "End line to read until. It is 1 indexed.",
                },
            },
            "required": ["file_path", "start_line", "end_line"],
            "additionalProperties": False,
        }
    ),
)
