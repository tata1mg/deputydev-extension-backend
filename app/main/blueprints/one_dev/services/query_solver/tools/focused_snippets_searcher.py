import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

FOCUSED_SNIPPETS_SEARCHER = ConversationTool(
    name="focused_snippets_searcher",
    description=textwrap.dedent("""
        This is a built-in tool.
        Searches the codebase for specific code definitions or snippets based on a given class name or function name.
        View the content of a code item node, such as a class or a function in a file using a fully qualified code item name.
        Use this tool to retrieve relevant code snippets that contain or define the specified search terms.
        You can provide multiple search terms at once, and the tool will return the most relevant code snippets for each.
        The search can be good for finding specific code snippets related to a class or function in the codebase, and therefore should ideally be used to
        search for specific code snippets rather than general code search queries. Also, it works best when there is ground truth in the search term, i.e.
        the search term is valid class or function name in the codebase (for eg. search terms directly picked from the relevant code snippets).

        If search term is not valid in the codebase, it would basically work as a lexical search and return the code snippets containing the search term or containing similar terms.

        ### Expected Input Format:
        Each search term should include:
        - A **keyword**: The name of the class or function to search for.
        - A **type**: Must be one of 'class', or 'function' to specify what is being searched.
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
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "search_terms": JSONSchema(
                type="array",
                description="A list of search terms, each containing a keyword, its type, and an optional file path.",
                items=JSONSchema(
                    type="object",
                    properties={
                        "keyword": JSONSchema(
                            type="string",
                            description="The search keyword, which can be a class or function name whose content needs to be searched.",
                        ),
                        "type": JSONSchema(
                            type="string",
                            enum=["class", "function"],
                            description="Specifies the type of the keyword being searched. Allowed values: 'class' or 'function'.",
                        ),
                        "file_path": JSONSchema(
                            type="string",
                            description="The file path where the search term is located (optional).",
                        ),
                    },
                    required=["keyword", "type"],
                ),
            ),
            "repo_path": JSONSchema(
                type="string",
                description="The absolute path to the root of the repository.",
            ),
        },
        required=["search_terms", "repo_path"],
    ),
)
