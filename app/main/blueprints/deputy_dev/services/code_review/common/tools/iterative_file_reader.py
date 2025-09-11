from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

ITERATIVE_FILE_READER = ConversationTool(
    name="iterative_file_reader",
    description="""
        Reads content of a file from a given start line number (1 indexed) to an end line number (1 indexed).
        This tool is designed for efficient iterative file reading with smart chunking strategies.
        
        CORE CAPABILITIES:
        - Reads up to 100 lines per call (enforced limit)
        - Supports targeted reading based on line numbers
        
        EFFICIENT READING STRATEGIES:
        
        1. ALWAYS START WITH LARGER CHUNKS (100 lines minimum recommended):
           - For unknown files: Start with lines 1-100, then 101-200, etc.
           - For targeted reading: Read 100-line windows around your target area
           - Avoid small chunks (20-50 lines) unless you know exactly what you need
        
        2. SMART TARGETING FOR PR REVIEWS:
           - If reviewing changes at line 188: Read lines 100-200 first (covers context)
           - If change is at line 45: Read lines 1-100 (captures imports + context)
           - Always prefer reading AROUND the change area, not FROM the beginning
        
        3. CONTEXT-AWARE CHUNKING:
           - For code files: Try to read complete functions/classes in one call
           - For imports: Read first 50-100 lines to capture all import statements
           - For specific functions: Calculate approximate line ranges and read entirely
        
        4. PROGRESSIVE EXPANSION:
           - If you need more context after initial read, expand in 100-line increments
           - Example: Read 100-200, then if needed 50-250 (overlapping for continuity)
           - Don't restart from line 1 unless specifically analyzing file structure
        
        5. TERMINATION CONDITIONS:
           - Stop reading when you have sufficient context for your task
           - The response explicitly indicates if end of file is reached
           - Don't continue reading if you found what you were looking for

        
        BEST PRACTICES FOR PR REVIEWS:
        - Identify changed line numbers first
        - Calculate optimal reading windows around changes
        - Read imports/dependencies if needed for context
        - Focus on modified functions/classes and their immediate context
        - Use overlapping reads only when necessary for continuity
        - Avoid making many iterations for a single file
        
        Remember: Each call has cost implications. Maximize information per call while minimizing total iterations.
    """,
    input_schema=JSONSchema(
        **{
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The complete path of the file relative to the repo root",
                },
                "start_line": {
                    "type": "number",
                    "description": "Start line to read from. It is 1 indexed.",
                },
                "end_line": {
                    "type": "number",
                    "description": "End line to read until. It is 1 indexed.",
                },
            },
            "required": ["file_path", "start_line", "end_line"],
        }
    ),
)
