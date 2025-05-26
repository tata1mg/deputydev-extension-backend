from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

TASK_COMPLETION = ConversationTool(
    name="task_completion",
    description="""
        Use this tool to signal that a task or workflow is finished, failed, or in some other state.
        The model should call this function with an appropriate status and summary message when the work is done or cannot proceed.
        This helps the client know when to stop or handle errors.
        If **replace_in_file** fails multiple times, it is recommended to call this tool with status as 'failed' and a message indicating the reason for failure rather than retrying the same tool.
    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Overall result of the task",
                    "enum": ["completed", "failed", "partial"],
                },
                "message": {
                    "type": "string",
                    "description": "Short human-readable summary (e.g., what was done or why it failed).",
                },
            },
            "required": ["status", "message"],
            "additionalProperties": False,
        }
    ),
)
