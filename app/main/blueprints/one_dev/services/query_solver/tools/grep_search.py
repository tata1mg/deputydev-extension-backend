from app.backend_common.services.llm.dataclasses.main import ConversationTool

GREP_SEARCH = ConversationTool(
    name="grep_search",
    description="""
        Searches for files in a given directory path.
        It is very important to provide the correct and complete directory path to search in, otherwise the tool will return the results from the repo root.
        This can also be used to list down files in a given directory.
        This gives at max 100 files.
    """,
    input_schema={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "The complete path of the directory to search in",
            },
        },
        "required": ["directory"],
    },
)
