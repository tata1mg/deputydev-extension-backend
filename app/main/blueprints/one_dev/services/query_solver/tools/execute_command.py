import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

EXECUTE_COMMAND = ConversationTool(
    name="execute_command",
    description=textwrap.dedent("""
        This is a built-in tool.
        Multiple instances of this tool should not be run in parallel.
        Executes a CLI command in the current working directory of the project.
        
        This tool is used to perform system-level operations such as building projects,
        starting development servers, running scripts, or installing dependencies.
        
        The command should be properly formatted for the user's OS and shell.
        If the task requires a different directory, include `cd` and use chaining (`&&`) 
        to ensure execution from that location.

        Only one command can be executed per invocation. Commands are run in an isolated 
        terminal environment and do not share state across invocations.

        Be cautious: Some commands may be destructive or require elevated privileges. 
        Use the `requires_approval` flag to indicate if explicit user consent is needed.
        Use the `is_long_running` flag to indicate if the command is expected to take a long time.

        If a command may invoke a pager (such as `git`, `less`, `man`, etc.), you must modify 
        the command to disable it. You can do this by adding options like `--no-pager` (e.g., `git --no-pager`) 
        or by piping the output through `cat` (e.g., `man ls | cat`). This ensures that output 
        is streamed directly and not buffered or paginated.

        Also ensure that the command does not require any user input or interaction if possible.

        Do not use this tool for tasks like writing code, or creating or updating files.  (IMPORTANT)
        
        The tool will return the terminal output in response.
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "command": JSONSchema(
                type="string",
                description=(
                    "The CLI command to execute. It should be valid for the user's OS/shell, "
                    "and include `cd <dir> && <command>` if execution requires changing directories. "
                    "Avoid unsafe operations unless absolutely necessary."
                ),
            ),
            "requires_approval": JSONSchema(
                type="boolean",
                description=(
                    "Whether this command requires explicit user approval. "
                    "Set to true for operations like installing packages, deleting data, "
                    "network actions, or anything with potential side effects. "
                    "Set to false for safe operations like reading files, listing contents, or starting a dev server."
                ),
            ),
            "is_long_running": JSONSchema(
                type="boolean",
                description=(
                    "Indicates if the command is expected to take a long time to complete. "
                    "Set to true for operations like builds, server startups, or installations; "
                    "false for quick tasks like listing files or checking status."
                ),
            ),
        },
        required=["command", "requires_approval", "is_long_running"],
    ),
)
