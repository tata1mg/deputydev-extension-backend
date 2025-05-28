from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

GREP_SEARCH = ConversationTool(
    name="grep_search",
    description="""
    This tool searches the content in all the files in a given directory path for specified search terms.
    
    BEST FOR:
    - Finding all references to functions, classes, or variables
    - Locating specific code patterns or strings
    - Discovering dependencies and usage patterns
    
    USAGE GUIDELINES:
    - Use EXACT identifiers from the code (function names, class names, variable names)
    - Do NOT add quotes, wildcards or regex symbols unless you specifically need them
    - For function/method searches, search for the bare name without parentheses
    - For multi-word searches, use quotes: "search term with spaces"
    
    EXAMPLES:
    - To find all uses of function 'calculate_total': grep_search("calculate_total")
    - To find a specific error string: grep_search("InvalidOperationError")
    - To find specific import: grep_search("from models import User")
    
    Note: For accurate results, always use exact syntax from the source code (e.g., function or variable names). Avoid adding or removing underscores, changing casing, or converting identifiers into plain English phrases.

    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "The complete path of the directory to search in",
                },
                "search_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of search terms to match against file names. ",
                },
            },
            "required": ["directory_path", "search_terms"],
        }
    ),
)
