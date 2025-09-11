import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

WRITE_TO_FILE = ConversationTool(
    name="write_to_file",
    description=textwrap.dedent("""
        Request to write content to a file at the specified path. If the file exists, it will be overwritten with the provided content. If the file doesn't exist, it will be created. This tool will automatically create any directories needed to write the file.
        This is a built-in tool. This should not be called in parallel for same file path.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "path": JSONSchema(
                type="string",
                description=(
                    "The path of the file to modify or new file path (relative to the current working directory of the project). "
                    "Only one file can be modified at a time."
                    "If you need to modify multiple files, invoke this tool multiple times, once for each file."
                ),
            ),
            "diff": JSONSchema(
                type="string",
                description="The content to write to the file. ALWAYS provide the COMPLETE intended content of the file, without any truncation or omissions. You MUST include ALL parts of the file, even if they haven't been modified.",
            ),
        },
        required=["path", "diff"],
    ),
)
