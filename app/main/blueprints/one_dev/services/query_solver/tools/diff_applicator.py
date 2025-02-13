from app.backend_common.services.llm.dataclasses.main import ConversationTool

DIFF_APPLICATOR = ConversationTool(
    name="diff_applicator",
    description="""
        This tool applies the given diff on the codebase. The diff should be in the unified diff format.
    """,
    input_schema={
        "type": "object",
        "properties": {
            "diff": {
                "type": "string",
                "description": "The diff to apply on the codebase. Should be in the unified diff format",
            },
        },
        "required": ["diff"],
    },
)
