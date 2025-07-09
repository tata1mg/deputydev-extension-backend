from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

ASK_USER_INPUT = ConversationTool(
    name="ask_user_input",
    description="""
        This is a built-in tool.
        This tool cannot be run in Parallel.
        This tool asks user any input if needed. This can be used to clear doubts, get user's view etc.
        It requires to send a prompt to be shown to the user. After which the user will reply basis the previous context and the given prompt.
    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to be shown to the user. This can be a question, a message or any other information",
                },
            },
            "required": ["prompt"],
        }
    ),
)
