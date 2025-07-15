import textwrap

from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

GREP_SEARCH = ConversationTool(
    name="grep_search",
    description=textwrap.dedent(
        """
        This is a built-in tool.
        This tool can be used in parallel only with other grep search calls.
        Use git grep or standard grep to find exact pattern matches within files or directories.

        This tool searches for specific text patterns inside files within a given path. It supports both plain text and regular expression queries.

        Results are returned in XML format. Each match includes:
        - The file path and matching line number
        - The matched line
        - Up to 2 lines of surrounding context

        For accurate results, always use the exact syntax as it appears in the source (e.g., exact function names, variables).
        Avoid changing case or format unless you explicitly set case-insensitive mode.

        Note: Total results are capped at 50.
        """
    ),
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
