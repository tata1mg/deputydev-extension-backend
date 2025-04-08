from app.backend_common.services.llm.dataclasses.main import ConversationTool

ITERATIVE_FILE_READER = ConversationTool(
    name="iterative_file_reader",
    description="""
        Reads a block of lines from a given file. Reads max 100 lines at a time.
        This tool can be used iteratively to read a file in chunks by just providing the offset line.
        To use this, only 2 things are needed, the file path and optionally, an offset line to start reading from.
    """,
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The complete path of the file relative to the repo root",
            },
            "line_offset": {
                "type": "number",
                "description": "Offset line to start reading from. If not provided, it will start from the beginning of the file.",
            },
        },
        "required": ["file_path"],
    },
)
