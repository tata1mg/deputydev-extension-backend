from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

ITERATIVE_FILE_READER = ConversationTool(
    name="iterative_file_reader",
    description="""
        Reads content of a file from a given start line number (1 indexed) to an end line number (1 indexed).
        This tool can be used iteratively to read a file in chunks by just providing the offset line.
        At once, it can read maximum of 100 lines.
        If you do not know the end line number, just provide the end line number as start_line + 100.
        It will let you know if the end of the file is reached.
        To use this, a valid file path is required.
        If you are not confident about import statements, then you can use this tool to read initial lines of the file to check imports.
        
        EFFICIENT USAGE:
        - Calculate precisely which line ranges you need before calling
        - Request 50-100 lines at once when appropriate
        - Read entire functions/methods in a single call when possible
        - Track where you left off to continue reading larger files

        Try to use this tool iteratively, to read a file until either the desired context is found or the end of the file is reached.
        The response will EXPLICITLY mention if the end of the file is reached or not.
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
        }
    ),
)
