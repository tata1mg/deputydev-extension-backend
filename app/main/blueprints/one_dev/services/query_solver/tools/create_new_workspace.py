from app.backend_common.services.llm.dataclasses.main import ConversationTool

CREATE_NEW_WORKSPACE = ConversationTool(
    name="create_new_workspace",
    description="""
        Get steps to help the user create any project in a Visual Studio Code workspace.

        This tool is used to assist users in setting up a new project environment in VS Code 
        based on a high-level query. It guides users through selecting appropriate technologies, 
        frameworks, and configurations to kickstart projects such as:
        - TypeScript apps
        - React apps
        - Python apps
        - Node.js apps
        - Java apps
        - Model Context Protocol (MCP) servers
        - VS Code extensions
        - Next.js or Vite frontends
        - Or any other developer-focused templates

        This tool is intended to be used as the first step when the user expresses intent to start
        a new coding project. It does not create the project directly but returns instructions and
        metadata to scaffold it manually or with follow-up automation. 

        make sure, if you need to create new files after successfully creating a workspace, you send send code blocks with <is_diff>true</is_diff> only
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
