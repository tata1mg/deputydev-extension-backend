from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

GREP_SEARCH = ConversationTool(
    name="grep_search",
    description="""
    This tool searches the content in all the files in a given directory path for specified search terms. It uses grep to perform the search.
    It does pattern matching on the file contents recursively. This can be used to search for specific patterns/words/sentences/keywords on the files in a directory in a very quick and efficient way.
    This tool reads the contents of the files and returns the lines that match the search terms.
    This should be used for queries that require to find specific pattern in the files, or which require a find and replace operation.
    
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
