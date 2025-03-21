from app.backend_common.services.llm.dataclasses.main import ConversationTool

FILE_PATH_SEARCHER = ConversationTool(
    name="file_path_searcher",
    description="""
        Searches for files with given search terms in a given directory (relative to repo root).
        This tool uses fuzzy search to match the search terms with the parts of file paths.
        This can also be used to list down files in a given directory if no search terms are provided.
        This gives at max 100 files.
    """,
    input_schema={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "The directory to search in, relative to the repo root. If not provided, the search will be done on the entire codebase",
            },
            "search_terms": {
                "type": "array",
                "items": {
                    "type": "string",
                },
                "description": "The search terms to search for in the file paths. If not provided, all files in the directory will be listed",
            },
        },
        "required": ["directory"],
    },
)
