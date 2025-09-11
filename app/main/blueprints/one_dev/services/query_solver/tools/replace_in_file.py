from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

REPLACE_IN_FILE = ConversationTool(
    name="replace_in_file",
    description="""This is a built-in tool. 
This is not meant to be run in parallel for the same file path.
Request to replace sections of content in an existing file using SEARCH/REPLACE blocks that define exact changes to specific parts of the file. 
This tool should be used when you need to make targeted changes to specific parts of a file.
Make sure you give all search/replace blocks for a single file in a single request.
The tool response will tell you if the changes were successful or not.
If tool fails, first try reading the file using other tools like iterative file reader to check latest file content and then re-run the tool with the latest file content.

## Example 1: Requesting to make targeted edits to a file

path: src/components/App.tsx
diff:
------- SEARCH
import React from 'react';
=======
import React, { useState } from 'react';
+++++++ REPLACE

------- SEARCH
function handleSubmit() {
  saveData();
  setLoading(false);
}

=======
+++++++ REPLACE

------- SEARCH
return (
  <div>
=======
function handleSubmit() {
  saveData();
  setLoading(false);
}

return (
  <div>
+++++++ REPLACE
""",
    input_schema=JSONSchema(
        type="object",
        properties={
            "path": JSONSchema(
                type="string",
                description=(
                    "The path of the file to modify (relative to the current working directory of the project). "
                    "Only one file can be modified at a time. If you need to modify multiple files, invoke this tool "
                    "multiple times, once for each file."
                ),
            ),
            "diff": JSONSchema(
                type="string",
                description=(
                    "One or more SEARCH/REPLACE blocks following this exact format:\n\n"
                    "------- SEARCH\n"
                    "[exact content to find]\n"
                    "=======\n"
                    "[new content to replace with]\n"
                    "+++++++ REPLACE\n\n"
                    "Critical rules:\n"
                    "1. SEARCH content must match the associated file section to find EXACTLY:\n"
                    "   * Match character-for-character including whitespace, indentation, line endings\n"
                    "   * Include all comments, docstrings, etc.\n"
                    "2. SEARCH/REPLACE blocks will ONLY replace the first match occurrence.\n"
                    "   * Include multiple unique SEARCH/REPLACE blocks if you need to make multiple changes.\n"
                    "   * Include *just* enough lines in each SEARCH section to uniquely match each set of lines that need to change.\n"
                    "   * When using multiple SEARCH/REPLACE blocks, list them in the order they appear in the file.\n"
                    "3. Keep SEARCH/REPLACE blocks concise:\n"
                    "   * Break large SEARCH/REPLACE blocks into a series of smaller blocks that each change a small portion of the file.\n"
                    "   * Include just the changing lines, and a few surrounding lines if needed for uniqueness.\n"
                    "   * Do not include long runs of unchanging lines in SEARCH/REPLACE blocks.\n"
                    "   * Each line must be complete. Never truncate lines mid-way through as this can cause matching failures.\n"
                    "4. Special operations:\n"
                    "   * To move code: Use two SEARCH/REPLACE blocks (one to delete from original + one to insert at new location)\n"
                    "   * To delete code: Use empty REPLACE section"
                ),
            ),
        },
        required=["path", "diff"],
        additionalProperties=False,
    ),
)
