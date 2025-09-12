from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

FILE_PATH_SEARCHER = ConversationTool(
    name="file_path_searcher",
    description="""
        Searches for files with given search terms in a given directory path.
        It is very important to provide the correct and complete directory path to search in, otherwise the tool will return the results from the repo root.
        This tool uses fuzzy search to match the search terms with the parts of file paths.
        This can also be used to list down files in a given directory if no search terms are provided.
        This gives at max 100 files.
    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "The complete path of the directory",
                },
                "search_terms": JSONSchema(
                    type="array",
                    items=JSONSchema(type="string"),
                    description="The search terms to search for in the file paths. If not provided, all files in the directory will be listed",
                ),
            },
            "required": ["directory"],
        }
    ),
)
