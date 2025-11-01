import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

SEMANTIC_SEARCH = ConversationTool(
    name="semantic_search",
    description=textwrap.dedent("""
        Searches the repository semantically to find code snippets relevant to a given query.
        Uses vector-based understanding to match code by meaning and intent, not exact text.
        Optionally, limit the search scope to specific paths. Include an explanation to help
        filter results based on reasoning or purpose.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "query": JSONSchema(
                type="string",
                description="Natural-language or technical query describing what to find in the codebase.",
            ),
            "explanation": JSONSchema(
                type="string",
                description="Reasoning or intent behind the query to improve semantic filtering.",
            ),
            "paths": JSONSchema(
                type="array",
                items=JSONSchema(type="string"),
                description="Optional: Relative directory paths to restrict the search scope.",
            ),
            "repo_path": JSONSchema(
                type="string",
                description="Absolute path to the root of the repository.",
            ),
        },
        required=["query", "explanation", "repo_path"],
        additionalProperties=False,
    ),
)
