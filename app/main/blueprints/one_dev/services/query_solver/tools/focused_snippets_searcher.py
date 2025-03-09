from app.backend_common.services.llm.dataclasses.main import ConversationTool

FOCUSED_SNIPPETS_SEARCHER = ConversationTool(
    name="focused_snippets_searcher",
    description="""
        Searches the codebase for specific code definitions or snippets based on given classname, function name or file name.
        This tool will do a search on the codebase and return the most relevant code snippets based on the given query.
        You can give multiple queries to search for multiple code snippets at once.
    """,
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"type": {"type": "string"}, "value": {"type": "string"}},
                    "required": ["type", "value"],
                },
            }
        },
        "required": ["query"],
    },
)
