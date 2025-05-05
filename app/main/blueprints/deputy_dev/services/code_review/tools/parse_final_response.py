from app.backend_common.services.llm.dataclasses.main import ConversationTool

PARSE_FINAL_RESPONSE = ConversationTool(
    name="parse_final_response",
    description="""
        When the LLM has gathered all necessary code context and is ready to provide the final review comments,
        it should call this tool with the complete review in XML format. The XML must match the format
        previously used (a <review> root with nested <comments> and one <comment> per finding,
        including file paths, line numbers, messages, and confidence/severity attributes).
        
        This tool should only be called when the LLM has finished gathering all the necessary information and is ready to provide the final review.
    """,
    input_schema={
            "type": "object",
            "properties": {
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
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
                            "description": "line on which comment is relevant. get this value from `<>` block at each code start in input pr diff. Return the exact value present with label `+` or `-`",
                        },
                        "confidence_score": {
                            "type": "number",
                            "description": "Float value from 0.0 to 1.0 indicating confidence level.",
                        },
                        "bucket": {
                            "type": "string",
                            "description": "Bucket name or label provided by LLM.",
                        }
                    },
                    "required": [
                        "description", "corrective_code", "file_path",
                        "line_number", "confidence_score", "bucket"
                    ]
                }
            }
        },
            "required": ["comments"]
        },
) 