import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

PUBLIC_URL_CONTENT_READER = ConversationTool(
    name="public_url_content_reader",
    description=textwrap.dedent("""
        This is a built-in tool.
        Fetches and converts content from publicly accessible HTTP/HTTPS URLs into clean, readable Markdown.

        Supports common web content types including HTML pages, text files, and public documentation. 
        Ideal for extracting readable content from blogs, articles, or developer docs.

        Returns the entire processed content in Markdown format (no chunking applied).

        Note: Only works with publicly accessible URLs. Do not use for private or access-restricted content 
        (e.g., Jira, Confluence, or internal portals).

        Tip: For best performance, process 3-5 URLs at a time.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "urls": JSONSchema(
                type="array",
                items=JSONSchema(
                    type="string",
                    format="uri",
                    pattern="^https?://",
                ),
                description="A list of publicly accessible HTTP/HTTPS URLs (maximum: 5).",
                maxItems=5,
            ),
        },
        required=["urls"],
    ),
)
