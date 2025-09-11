from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

RELATED_CODE_SEARCHER = ConversationTool(
    name="related_code_searcher",
    description="""
        Searches the codebase for relevant code snippets based on the given query.
        This tool does a vector + lexical hybrid search on the chunks on the entire codebase and then returns the ones which are relevant to the query.
        This tool also optionally takes a list of paths to limit the scope of the search.
        This performs best when the search query is more precise and relating to the function or purpose of code. Results will be poor if asking a very broad question, such as asking about the general 'framework' or 'implementation' of a large component or system.
    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "The search query to search the codebase for. Include relevant keywords and code snippets for best results",
                },
                "paths": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "The paths to limit the search to. If not provided, the search will be done on the entire codebase",
                },
            },
            "required": ["search_query"],
        }
    ),
)
