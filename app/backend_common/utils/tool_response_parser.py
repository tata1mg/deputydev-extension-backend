from typing import Any, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from pydantic import ValidationError

from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClassFocusItem,
    CodeSnippetFocusItem,
    DirectoryFocusItem,
    FileFocusItem,
    FocusItem,
    FunctionFocusItem,
    UrlFocusItem,
)


class LLMResponseFormatter:
    """
    Utility to convert internal tool responses into Markdown-formatted strings
    for feeding into LLM prompts.
    """

    @staticmethod
    def format_iterative_file_reader_response(response: Dict[str, Any]) -> str:
        """
        Convert an IterativeFileReaderResponse into a detailed Markdown chunk for LLM input.
        """
        chunk = response["chunk"]
        file_path = chunk["source_details"]["file_path"]
        start = chunk["source_details"]["start_line"]
        end = chunk["source_details"]["end_line"]
        eof_reached = response["eof_reached"]
        was_summary = response["was_summary"]
        total_lines = response["total_lines"]
        raw_content = chunk["content"]

        # --- Header with metadata ---
        header_lines = [
            f"### File: `{file_path}`",
            f"- Lines read: **{start}-{end}**",
            f"- Total lines in file: **{total_lines}**",
            f"- Content type: {'Summary' if was_summary else 'Raw snippet'}",
            f"- End of file reached: {'Yes' if eof_reached else 'No'}",
        ]

        header = "\n".join(header_lines)

        formatted_content = raw_content

        # --- Content block ---
        if formatted_content:
            content_block = f"\n\n```\n{formatted_content}\n```"
        else:
            content_block = "\n\n No content read from the file."

        # --- Footer note ---
        if was_summary:
            footer = "\n\n Note: The file was too large to load completely, so a summary was provided instead."
        elif eof_reached:
            footer = "\n\n You have reached the end of the file."
        else:
            footer = "\n\n This is a partial read; more content may follow."

        return f"{header}{content_block}{footer}"

    # ---------------------------------------------------------------------
    # GREP TOOL FORMATTER
    # ---------------------------------------------------------------------
    @staticmethod
    def format_grep_tool_response(response: Dict[str, Any]) -> str:
        """
        Convert a GrepToolResponse into a detailed Markdown chunk for LLM input.
        """
        results: List[Dict[str, Any]] = response.get("data", []) or []
        search_term = response.get("search_term", "N/A")
        directory_path = response.get("directory_path", "N/A")
        case_insensitive = response.get("case_insensitive", False)
        use_regex = response.get("use_regex", False)

        case = "Case-insensitive" if case_insensitive else "Case-sensitive"
        total_hits = len(results)

        # --- Overall header ---
        header_lines = [
            "### Grep Search Results",
            f"- Search query: `{search_term}`",
            f"- Regex: {'Yes' if use_regex else 'No'}",
            f"- Case: **{case}**",
            f"- Scope: `{directory_path}`",
            f"- Results: **{total_hits}**"
            + (" (truncated at 50 results — try refining your search for more precision)" if total_hits >= 50 else ""),
        ]
        header = "\n".join(header_lines)

        # --- Empty results case ---
        if total_hits == 0:
            return f"{header}\n\nNo matches found."

        note = "\nNote: A `*` in the gutter marks a matched line."  # Legend for matched lines
        # --- Per-result sections ---
        sections: List[str] = []
        for idx, item in enumerate(results, start=1):
            try:
                chunk: ChunkInfo = ChunkInfo(**item["chunk_info"])
            except ValidationError as e:
                raise ValueError(f"Invalid chunk_info structure at index {idx}: {e}")
            src: ChunkSourceDetails = chunk.source_details
            file_path: str = src.file_path
            start: int = src.start_line
            end: int = src.end_line
            raw_content: str = chunk.content or ""

            # Handle both "matched_line" and "matched_lines"
            ml = item.get("matched_lines", item.get("matched_line", []))
            if isinstance(ml, int):
                matched_lines = [ml]
            else:
                matched_lines = sorted(set(ml or []))

            # Number and lightly highlight matched lines
            lines = raw_content.splitlines()
            matched_set = set(matched_lines)

            # Legend: "*" marks matched lines in the gutter

            # No line numbers, just mark matched lines with "*"
            guttered_lines: List[str] = []
            for i, line in enumerate(lines):
                ln = start + i
                marker = "*" if ln in matched_set else " "
                guttered_lines.append(f"{marker}   {line}")

            section_header = [
                f"#### Result {idx} — `{file_path}`",
                f"- Lines: **{start}-{end}**",
                f"- Matched lines: {', '.join(map(str, matched_lines)) if matched_lines else '—'}",
            ]
            section = "\n".join(section_header)
            joined_lines = "\n".join(guttered_lines)
            code_block = f"\n```\n{joined_lines}\n```"

            sections.append(section + code_block)

        return f"{header}\n\n" + "\n\n".join(sections) + note

    # ---------------------------------------------------------------------
    # ASK USER INPUT TOOL FORMATTER (structured return)
    # ---------------------------------------------------------------------
    @staticmethod
    def format_ask_user_input_response(
        response: Dict[str, Any], vscode_env: Optional[str], focus_items: Optional[List[FocusItem]]
    ) -> Dict[str, Any]:
        # user response (just the raw user response string/dict)
        user_response = response["user_response"] if response["user_response"] else ""
        # focus_items string builder
        focus_parts: List[str] = []
        if focus_items:
            # Code-related focus items
            code_snippet_based_items = [
                item
                for item in focus_items
                if isinstance(item, (CodeSnippetFocusItem, FileFocusItem, ClassFocusItem, FunctionFocusItem))
            ]
            if code_snippet_based_items:
                snippet_text = "The user has asked to focus on the following:\n"
                for focus_item in code_snippet_based_items:
                    snippet_text += (
                        "<item>"
                        + f"<type>{focus_item.type.value}</type>"
                        + (f"<value>{focus_item.value}</value>" if getattr(focus_item, "value", None) else "")
                        + f"<path>{focus_item.path}</path>"
                    )
                    if getattr(focus_item, "chunks", None):
                        snippet_text += "".join([chunk.get_xml() for chunk in focus_item.chunks])
                    snippet_text += "</item>\n"
                focus_parts.append(snippet_text)

            # Directory items
            directory_items = [item for item in focus_items if isinstance(item, DirectoryFocusItem)]
            if directory_items:
                dir_text = "\nThe user has also asked to explore the contents of the following directories:\n"
                for directory_item in directory_items:
                    dir_text += "<item><type>directory</type>" + f"<path>{directory_item.path}</path><structure>\n"
                    for entry in directory_item.structure or []:
                        label = "file" if entry.type == "file" else "folder"
                        dir_text += f"{label}: {entry.name}\n"
                    dir_text += "</structure></item>\n"
                focus_parts.append(dir_text)

            # URL items
            url_focus_items = [item for item in focus_items if isinstance(item, UrlFocusItem)]
            if url_focus_items:
                urls = [url.url for url in url_focus_items]
                focus_parts.append(f"\nThe user has also provided the following URLs for reference: {urls}\n")

        focus_items_str = "\n".join(focus_parts).strip() if focus_parts else ""

        # vscode_env string (already formatted)
        vscode_env_str = (
            f"""
====
Below is the information about the current vscode environment:
{vscode_env}
====
"""
            if vscode_env
            else ""
        )

        return {"user_response": user_response, "focus_items": focus_items_str, "vscode_env": vscode_env_str.strip()}
