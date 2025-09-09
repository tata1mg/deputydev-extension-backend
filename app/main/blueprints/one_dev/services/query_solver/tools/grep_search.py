import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

GREP_SEARCH = ConversationTool(
    name="grep_search",
    description=textwrap.dedent("""
        A built-in tool for searching text patterns inside files within a specified directory.

        **Capabilities:**
        - Uses `ripgrep` under the hood for fast, recursive text search.
        - Supports both exact string matches and regular expressions.
        - Returns results in plain Markdown format.
        - Each result includes:
            - File path and matching line number
            - The matched line
            - Up to 2 lines of surrounding context (above and below)
        - Can locate function names, variable assignments, configuration keys, comments, and more.

        **Notes:**
        - For accurate results, use the exact syntax and casing as it appears in the source, unless case-insensitive mode is explicitly enabled.
        - Results are capped at 50 matches.
        - #IMPORTANT: This tool is for file contents only; it does not search directory names or metadata.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "search_path": JSONSchema(
                type="string",
                description="The relative path to search. This can be a directory or a file. This is a required parameter. Use '.' for the project's root directory.",
            ),
            "query": JSONSchema(type="string", description="The search term or pattern to look for within files."),
            "case_insensitive": JSONSchema(type="boolean", description="If true, performs a case-insensitive search."),
            "use_regex": JSONSchema(
                type="boolean",
                description="If true, treats the query as a regular expression. If false, uses fixed string matching.",
            ),
            "repo_path": JSONSchema(
                type="string",
                description="The absolute path to the root of the repository.",
            ),
        },
        required=["search_path", "query", "case_insensitive", "use_regex", "repo_path"],
    ),
)
