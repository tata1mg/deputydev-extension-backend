import textwrap
from typing import Optional

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema


def get_create_new_workspace_tool(write_mode: Optional[bool] = False) -> ConversationTool:
    description = textwrap.dedent("""
        This is a built-in tool.
        This tool should not be run in parallel with any tool. This must be given as a single tool request.
        Assist the user in scaffolding a brand-new workspace based on a high-level project request.
        Given a natural-language query (e.g. “Create a Next.js blog with TypeScript” or “Start a Vite React dashboard”, etc.),
        
        This tool is intended to be used as the first step when the user expresses intent to start
        a new coding project. This tool does not execute any command; it only outputs instructions and metadata.

        # Do not use this tool if the user is asking for help with an existing project or codebase, like "Fix this bug in my React app" or "How do I add a new route to my Express server?". (IMPORTANT)

        The tool will return the status of the workspace creation:
        - If the workspace is created successfully, then proceed next steps.
        - First think (a lot first step-by-step) about the initial project requirements , workspace structure and files, libraries needed for the project.
        - If the workspace requires additional libraries for setup or configuration, then use the `execute_command` tool.
        - Freely use other tools to complete the task.
    """)

    if write_mode:
        description += textwrap.dedent("""
        - If file-creation steps are needed in a follow-up, use the `write_to_file` tool for creating new files or the `replace_in_file` tool for modifying existing files.
        """)
    else:
        description += textwrap.dedent("""
        - If file-creation steps are needed, send a diff <code_block> with `is_diff` set to true in the response.
        """)

    return ConversationTool(
        name="create_new_workspace",
        description=description,
        input_schema=JSONSchema(
            type="object",
            properties={
                "query": JSONSchema(
                    type="string",
                    description=textwrap.dedent(
                        "A clear and concise description of the workspace or project the user wants to create. "
                        "This is a natural language request like 'Create a Next.js blog with TypeScript' or "
                        "'Start a Vite React project for a dashboard UI'."
                    ),
                ),
            },
            required=["query"],
        ),
    )
