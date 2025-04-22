from app.backend_common.services.llm.dataclasses.main import ConversationTool

"""A tool for executing bash commands.

This tool allows the agent to run shell commands and get their output.
Commands are executed in a controlled environment with appropriate safeguards.
Command filters can be added to transform commands before execution.
"""

BASH_TOOL = ConversationTool(
    name="bash",
    description="""\
        Run commands in a bash shell
        * When invoking this tool, the contents of the \"command\" parameter does NOT need to be XML-escaped.
        * You don't have access to the internet via this tool.
        * You do have access to a mirror of common linux and python packages via apt and pip.
        * State is persistent across command calls and discussions with the user.
        * To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
        * Please avoid commands that may produce a very large amount of output.
        * ls -R command is prohibited
        * Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.""",
    input_schema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to run.",
            },
        },
        "required": ["command"],
    }
)
