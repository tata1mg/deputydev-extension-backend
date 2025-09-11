import textwrap

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, JSONSchema

RESOLVE_IMPORT_TOOL = ConversationTool(
    name="resolve_import_tool",
    description=textwrap.dedent("""
        Resolve where an **external import** points to.

        Use for:
        • Stdlib modules: `import os` → `os`
        • Third-party libs: `import httpx`, `from dotenv import load_dotenv` → `load_dotenv`
        • Symbols from stdlib: `from pathlib import Path` → `Path`

        Do NOT use for repo-local code (e.g. `from manager.tools import define_tools`).
        For those, use **get_usage_tool** instead.

        Input notes
        -----
        • `import_name` is required (exact import identifier as it appears in the code).
        • `file_path` is required (absolute filesystem path).

        Output (shape expectation)
        --------------------------
        • `moduleTargets`: resolved files + line numbers  
        • `hoverTexts`: optional doc/signature info  
        • `definitions`: symbol bodies if resolvable  
        • `modulePreviews`: file snippets if no body  
        """),
    input_schema=JSONSchema(
        type="object",
        properties={
            "import_name": JSONSchema(type="string", description="Exact identifier being imported."),
            "file_path": JSONSchema(type="string", description="Absolute path of file containing the import."),
        },
        required=["import_name", "file_path"],
    ),
)
