from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema

PARSE_FINAL_RESPONSE = ConversationTool(
    name="parse_final_response",
    description="""
        When the LLM has gathered all necessary code context and is ready to provide the final review comments,
        it should call this tool with the complete review in given format without missing any field. 
        including file paths, line numbers, messages, and confidence/severity attributes).
        Note: 
        - For each finding or improvement, create a separate comment object within the comments.
        - If you find nothing to improve the PR, there should be no comment inside comments key and just return an empty array. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
        - Always make comment on (+) line number.

        This tool should only be called when the LLM has finished gathering all the necessary information and is ready to provide the final review.
        Always Provide response for this Tool in Tool Use Request block.
    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "comments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "A short one-line summary of the issue or suggestion.",
                            },
                            "tag": {
                                "type": "string",
                                "enum": ["bug", "suggestion"],
                                "description": "Classify the comment as either a 'bug' or a 'suggestion'.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the issue. Do not include code blocks.",
                            },
                            "corrective_code": {
                                "type": "string",
                                "description": "Corrective code suggestion. Rewrite or create new (in case of missing) code, docstring or documentation for developer to directly use it If there's no suggestion, return empty string.",
                            },
                            "file_path": {
                                "type": "string",
                                "description": "File path the comment is associated with.",
                            },
                            "line_number": {
                                "type": "string",
                                "description": "the line on which the comment is relevant. Extract this from the `<>` block at the start of each code snippet in the input. Return exactly the value labeled with “+”. Comments must be made only on added lines (“+”)",
                            },
                            "confidence_score": {
                                "type": "number",
                                "description": "Float value from 0.0 to 1.0 indicating confidence level.",
                            },
                            "bucket": {
                                "type": "string",
                                "description": "Bucket name or label provided by LLM.",
                            },
                            "rationale": {
                                "type": "string",
                                "description": "Reason or justification for raising the comment. This should explain why this is important or how it impacts the code quality or behavior.",
                            },
                        },
                        "required": [
                            "title",
                            "tag",
                            "description",
                            "corrective_code",
                            "file_path",
                            "line_number",
                            "confidence_score",
                            "bucket",
                            "rationale",
                        ],
                    },
                }
            },
            "required": ["comments"],
        }
    ),
)
