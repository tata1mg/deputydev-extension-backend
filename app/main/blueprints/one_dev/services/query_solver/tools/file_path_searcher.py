import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

FILE_PATH_SEARCHER = ConversationTool(
    name="file_path_searcher",
    description=textwrap.dedent("""
        This is a built-in tool.
        Searches for files with given search terms in a given directory path.
        It is very important to provide the correct and complete directory path to search in, otherwise the tool will return the results from the repo root.
        This tool uses fuzzy search to match the search terms with the parts of file paths.
        This can also be used to list down files in a given directory if no search terms are provided.
        This gives at max 100 files.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "directory": JSONSchema(
                type="string",
                description="The full path to the file, relative to the root of the repository.",
            ),
            "repo_path": JSONSchema(
                type="string",
                description="The absolute path to the root of the repository.",
            ),
            "search_terms": JSONSchema(
                type="array",
                items=JSONSchema(type="string"),
                description="The search terms to search for in the file paths. If not provided, all files in the directory will be listed",
            ),
        },
        required=["directory", "repo_path"],
    ),
)
