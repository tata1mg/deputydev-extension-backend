from app.backend_common.services.llm.dataclasses.main import ConversationTool

FOCUSED_SNIPPETS_SEARCHER = ConversationTool(
    name="focused_snippets_searcher",
    description="""
        Searches the codebase for specific code definitions or snippets based on a given class name, function name, or file name.
        Use this tool to retrieve relevant code snippets that contain or define the specified search terms. 
        You can provide multiple search terms at once, and the tool will return the most relevant code snippets for each.

        ### Expected Input Format:
        Each search term should include:
        - A **keyword**: The name of the class, function, or file to search for.
        - A **type**: Must be one of 'class', 'function', or 'file' to specify what is being searched.
        - An optional **file path**: To narrow down the search to a specific location in the codebase.

        ### Example Input:
        ```
        {
            "search_terms": [
                {
                    "keyword": "LeadManager",
                    "type": "class",
                    "file_path": "src/models/lead_manager.py"
                },
                {
                    "keyword": "serialize_feeds_data",
                    "type": "function"
                }
            ]
        }
        ```

        ### Explanation:
        - The first search term looks for the **class** named `LeadManager` in the file `src/models/lead_manager.py`.
        - The second search term looks for the **function** named `serialize_feeds_data` across the entire codebase.

        Use this tool whenever you need precise code snippets related to specific elements in the codebase.
    """,
    input_schema={
        "type": "object",
        "properties": {
            "search_terms": {
                "type": "array",
                "description": "A list of search terms, each containing a keyword, its type, and an optional file path.",
                "items": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "The search keyword, which can be a class, function, or file name whose content needs to be searched."
                        },
                        "type": {
                            "type": "string",
                            "description": "Specifies the type of the keyword being searched. Allowed values: 'class', 'function', or 'file'."
                        },
                        "file_path": {
                            "type": "string",
                            "description": "The file path where the search term is located (optional)."
                        }
                    },
                    "required": ["keyword", "type"]
                }
            }
        },
        "required": ["search_terms"]
    }
)
