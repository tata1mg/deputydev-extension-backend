from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

PR_REVIEW_PLANNER = ConversationTool(
    name="pr_review_planner",
    description="""
    This tool creates a comprehensive review plan by analyzing the PR diff, title, and description.
    It identifies modified elements (functions, classes, variables), even when only partial code is visible.
    It provides intelligent guesses about potentially affected areas and suggests specific tool calls for
    systematic investigation.

    Use this tool at the beginning of PR review to get a structured approach for investigating code changes.
    The tool will generate exploratory steps even when function/class names aren't explicitly visible in the diff.

    The output includes:
    1. Analysis of changed elements (both visible and inferred)
    2. Suggested investigation approach with specific tool calls
    3. Areas requiring special focus based on change patterns
    4. Heuristic-based identification of potentially affected areas
    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "review_focus": {
                    "type": "string",
                    "description": "Optional. Specific aspect to focus review on (security, performance, etc.), What all you want to look for in PR.",
                }
            },
            "required": ["review_focus"],
        }
    ),
)
