from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

GREP_SEARCH = ConversationTool(
    name="grep_search",
    description="""
    This tool searches for specific text patterns inside files within a given path. It supports both plain text and regular expression queries.
    
    BEST FOR:
    - Finding all references to functions, classes, or variables
    - Locating specific patterns or strings
    - Discovering dependencies and usage patterns
    
    USAGE GUIDELINES:
    - Use EXACT identifiers from the code (function names, class names, variable names)
    - Do NOT add quotes unless you specifically need them
    - For function/method searches, search for the bare name without parentheses
    - For multi-word searches, use quotes: "search term with spaces"
    
    EXAMPLES:
    - To find all uses of function 'calculate_total': grep_search("calculate_total")
    - To find a specific error string: grep_search("InvalidOperationError")
    - To find specific import: grep_search("from models import User")
    - To find a function with regular expression:
    grep_search("def calculate_[a-zA-Z_]+\\(.*\\):",case_insensitive=False, use_regex=True)
    - to find a code block with case insensitive search:
    grep_search("def calculate_total\\(.*\\):", case_insensitive=True, use_regex=True)
    
    Note: For accurate results, always use exact syntax from the source code (e.g., function or variable names). Avoid adding or removing underscores, changing casing, or converting identifiers into plain English phrases.
    Note: Total results are capped at 50.
    """,
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
        },
        required=["search_path", "query", "case_insensitive", "use_regex"],
    ),
)
