import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

ASK_USER_INPUT = ConversationTool(
    name="ask_user_input",
    description=textwrap.dedent("""
        This is a built-in tool.
        This tool should not be run in parallel with any tool. This must be given as a single tool request.
        This tool asks user any input if needed. This can be used to clear doubts, get user's view etc.
        If the user's query is a development focused query, do not end the chat to get the user's response. Instead give a tool use request for ask_user_input tool.
        This is very important.
        It requires to send a prompt to be shown to the user. After which the user will reply basis the previous context and the given prompt.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "prompt": JSONSchema(
                type="string",
                description="The prompt to be shown to the user. This can be a question, a message or any other information",
            ),
        },
        required=["prompt"],
    ),
)
