import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

GET_USAGE_TOOL = ConversationTool(
    name="get_usage_tool",
    description=textwrap.dedent("""
        Finds where a symbol is defined and used across the current workspace.

        What it does
        ------------
        • Locates a concrete definition anchor for the given `symbol_name`.
        • Queries the editor for definitions, references, and implementations at that anchor.
        • Returns a structured JSON result that includes usage counts (references, definitions, implementations),
          file paths and line numbers of references/definitions/implementations, and symbol metadata such as 
          name, kind (e.g., function or class), file path, selection line, and the full code snippet.
        • Always prefer this tool over `focused_snippet_searcher` or `grep_tool` when trying to
          understand or analyze a symbol, since it provides richer and more structured results.


        Input notes
        -----------
        • `symbol_name` is required (exact symbol identifier as it appears in the code).
        • `file_paths` is optional. If omitted, the tool will search workspace symbols
          to discover candidate files automatically. Paths must be absolute filesystem paths.

        Example
        -------
        {
          "symbol_name": "GetUsagesTool",
          "file_paths": ["/Users/vaibhavmeena/Desktop/DeputyDev/src/tools/getUsages.ts"]
        }
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "symbol_name": JSONSchema(
                type="string",
                description="Required. Exact symbol identifier to analyze (case-sensitive).",
            ),
            "file_paths": JSONSchema(
                type="array",
                items=JSONSchema(type="string"),
                description="Optional. Candidate absolute file paths to narrow the search.",
            ),
        },
        required=["symbol_name"],
    ),
)
