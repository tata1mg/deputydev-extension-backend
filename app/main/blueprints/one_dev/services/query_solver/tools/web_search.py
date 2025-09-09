import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

WEB_SEARCH = ConversationTool(
    name="web_search",
    description=textwrap.dedent("""
        This is a built-in tool.
        Performs a real-time, AI-powered web search using a **detailed, natural language prompt** that includes relevant context such as code snippets, error messages, intent, or technology stack.

        This tool should be used when:
        - The assistant needs updated documentation or APIs, or changelogs are needed.
        - The user reports an error or unexpected behavior in a library or framework.
        - The user is troubleshooting an issue with a library or framework.
        - The assistant lacks fresh or specific enough data.
        - A code pattern or implementation approach needs confirmation from recent best practices.
        - The assistant’s internal knowledge may be outdated or uncertain.
        - The question involves recent tech (e.g., new SDKs, AI tools, framework versions).
        - External resources like GitHub issues, Stack Overflow, or blog posts may offer better insights.

        **Strongly prefer using this tool by default when such context is available.**
        If there is any doubt about internal knowledge being stale, incomplete, or ambiguous — **always use this tool**.

        The input should include:
        - What the user is trying to achieve.
        - Any relevant code snippets or errors.
        - Specific tools, libraries, or frameworks involved.
        - Version or date context if relevant.
        - Optional domain hints (e.g., “check site:stackoverflow.com or site:fastapi.tiangolo.com”).

        Example Input:
        "I'm using FastAPI to stream large files to clients without loading them into memory. Here's my current approach using StreamingResponse (code snippet). I want to confirm if this is the most efficient method and if chunked transfer encoding is handled automatically. Please look for any recent best practices or documentation as of 2025."

        Example Input:
        "I'm getting 'psycopg2.OperationalError: could not connect to server' when running Django with Postgres in Docker Compose. I suspect it's due to race condition on startup. Please find a 2024-recommended solution or wait-for-it script alternatives."
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "descriptive_query": JSONSchema(
                type="string",
                description="Full, natural language prompt including user intent, code, errors, and context for the search.",
            ),
        },
        required=["descriptive_query"],
    ),
)
