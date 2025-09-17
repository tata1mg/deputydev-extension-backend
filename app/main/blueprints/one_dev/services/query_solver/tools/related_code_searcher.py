import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

RELATED_CODE_SEARCHER = ConversationTool(
    name="related_code_searcher",
    description=textwrap.dedent("""
        This is a built-in tool.

        Searches the repository for relevant code snippets based on the given query.
        This tool does a vector + lexical hybrid search on the chunks on the entire repository and then returns the ones which are relevant to the query.
        This tool also optionally takes a list of paths to limit the scope of the search.
        This performs best when the search query is more precise and relating to the function or purpose of code. Results will be poor if asking a very broad question, such as asking about the general 'framework' or 'implementation' of a large component or system.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "search_query": JSONSchema(
                type="string",
                description="The search query to search the repository for. Include relevant keywords and code snippets for best results.",
            ),
            "paths": JSONSchema(
                type="array",
                items=JSONSchema(type="string"),
                description="The relative paths to limit the search to. If not provided, the search will be done on the entire repository. [Optional]",
            ),
            "repo_path": JSONSchema(
                type="string",
                description="The absolute path to the root of the repository.",
            ),
        },
        required=["search_query", "repo_path"],
        additionalProperties=False,
    ),
)
