from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

REPLACE_IN_FILE = ConversationTool(
    name="replace_in_file",
    description="""This is a built-in tool. 
    This tool cannot be run in Parallel.
    Request to replace sections of content in an existing file using SEARCH/REPLACE blocks that define exact changes to specific parts of the file. 
This tool should be used when you need to make targeted changes to specific parts of a file.
Make sure you give all search/replace blocks for a single file in a single request.
The tool response will tell you if the changes were successful or not.
If tool fails, first try reading the file using other tools like iterative file reader to check latest file content and then re-run the tool with the latest file content.

    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "The path of the file to modify (relative to the current working directory of the project). Only one file can be modified at a time. "
                        "If you need to modify multiple files, invoke this tool multiple times, once for each file. "
                    ),
                },
                "diff": {
                    "type": "string",
                    "description": """
One or more SEARCH/REPLACE blocks following this exact format:

<<<<<<< SEARCH
[exact content to find]
=======
[new content to replace with]
>>>>>>> REPLACE

Critical rules:
1. SEARCH content must match the associated file section to find EXACTLY:
    * Match character-for-character including whitespace, indentation, line endings
    * Include all comments, docstrings, etc.
2. SEARCH/REPLACE blocks will ONLY replace the first match occurrence.
    * Including multiple unique SEARCH/REPLACE blocks if you need to make multiple changes.
    * Include *just* enough lines in each SEARCH section to uniquely match each set of lines that need to change.
    * When using multiple SEARCH/REPLACE blocks, list them in the order they appear in the file.
3. Keep SEARCH/REPLACE blocks concise:
    * Break large SEARCH/REPLACE blocks into a series of smaller blocks that each change a small portion of the file.
    * Include just the changing lines, and a few surrounding lines if needed for uniqueness.
    * Do not include long runs of unchanging lines in SEARCH/REPLACE blocks.
    * Each line must be complete. Never truncate lines mid-way through as this can cause matching failures.
4. Special operations:
    * To move code: Use two SEARCH/REPLACE blocks (one to delete from original + one to insert at new location)
    * To delete code: Use empty REPLACE section
                """,
                },
            },
            "required": ["path", "diff"],
            "additionalProperties": False,
        }
    ),
)
