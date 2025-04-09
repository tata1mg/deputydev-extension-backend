from app.backend_common.services.llm.dataclasses.main import ConversationTool

GREP_SEARCH = ConversationTool(
    name="grep_search",
    description="""
    Searches for the content of all files in a given directory path.
    It is very important to provide the correct and complete directory path to search in; otherwise, the tool will return results from the repo root.
    This tool reads the contents of the files and returns the lines that match the search terms.
""",
    input_schema={
        "type": "object",
        "properties": {
            "directory_path": {
                "type": "string",
                "description": "The complete path of the directory to search in",
            },
            "search_terms": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of search terms to match against file names.",
            },
        },
        "required": ["directory_path", "search_terms"],
    },
)
