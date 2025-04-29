from app.backend_common.services.llm.dataclasses.main import ConversationTool

CREATE_NEW_WORKSPACE = ConversationTool(
    name="create_new_workspace",
    description="""
        Assist the user in scaffolding a brand-new workspace based on a high-level project request.
        Given a natural-language query (e.g. “Create a Next.js blog with TypeScript” or “Start a Vite React dashboard”, etc.),
        
        This tool is intended to be used as the first step when the user expresses intent to start
        a new coding project.This tool does not execute any code; it only outputs instructions and metadata. 

        The tool will return the status of the workspace creation:
        - If the workspace is created successfully, then proceed next steps.
        - First think(a lot first step-by-step) inside <thinking> tag about the initial project requirements , workspace structure and files, libraries needed for the project.
        - If the workspace requires additional libraries for setup or configuration, then use the `execute_command` tool.
        - If file-creation steps are needed in a follow-up, emit code-block diffs annotated with `<is_diff>true</is_diff>`.
        - Freely use other tools to complete the task.

    """,
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "A clear and concise description of the workspace or project the user wants to create. "
                    "This is a natural language request like 'Create a Next.js blog with TypeScript' or "
                    "'Start a Vite React project for a dashboard UI'."
                ),
            },
        },
        "required": ["query"],
    },
)
