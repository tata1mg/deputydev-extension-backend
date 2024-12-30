from typing import Optional

from pydantic import BaseModel


class ChunkInfo(BaseModel):
    """
    Information about a chunk of code.

    Attributes:
        content (str): The content of the chunk.
        start (int): The starting line number of the chunk.
        end (int): The ending line number of the chunk.
        source (str): The source file of the chunk.
    """

    content: str
    start: int
    end: int
    source: str
    metadata: Optional[dict] = None

    def get_chunk_content(self, add_ellipsis: bool = True, add_lines: bool = True):
        """
        Get a content of the chunk.

        Args:
            add_ellipsis (bool, optional): Whether to add ellipsis (...) at the beginning and end of the snippet. Defaults to True.
            add_lines (bool, optional): Whether to prepend line numbers to each line of the snippet. Defaults to True.

        Returns:
            str: The snippet of the chunk.
        """
        snippet = "\n".join(
            (f"{i+1 + self.start}: {line}" if add_lines else line) for i, line in enumerate(self.content.splitlines())
        )
        if add_ellipsis:
            if self.start > 1:
                snippet = "...\n" + snippet
            if self.end < self.content.count("\n") + 1:
                snippet = snippet + "\n..."
        return snippet

    def get_chunk_content_with_meta_data(
        self, add_ellipsis: bool = True, add_lines: bool = True, add_class_function_info=True
    ):
        chunk_content = self.get_chunk_content(add_ellipsis, add_lines)
        if not self.metadata:
            return chunk_content

        meta_data = self.get_meta_data_notes(add_class_function_info)
        if meta_data:
            return f"<meta_data>{meta_data}\n</meta_data>\n<code>\n{chunk_content}\n</code>"
        else:
            return chunk_content

    def get_meta_data_notes(self, add_class_function_info):
        # prepare hierarchy
        chunk_final_meta_data = ""
        if add_class_function_info and self.metadata["all_classes"]:
            chunk_final_meta_data += (
                f"\n Below classes may use the imports in this snippet: \n {self.metadata['all_classes']}"
            )
        if add_class_function_info and self.metadata["all_functions"]:
            chunk_final_meta_data += (
                f"\n Below functions may use the imports in this snippet: \n {self.metadata['all_functions']}\n"
            )

        hierarchy_data = []
        hierarchy_seperator = "\t"

        for idx, hierarchy in enumerate(self.metadata["hierarchy"]):
            indent = hierarchy_seperator * idx
            hierarchy_data.append(f"{indent}{hierarchy['type']}  {hierarchy['value']}")
            hierarchy_data.append(f"{indent}{hierarchy_seperator}...")  # Add ellipsis at current indent level
        if hierarchy_data:
            chunk_final_meta_data += "Snippet hierarchy represented in pseudo code format: \n"
            chunk_final_meta_data += "\n".join(hierarchy_data)
            chunk_final_meta_data += "\n"
        return chunk_final_meta_data

    @property
    def denotation(self) -> str:
        """
        Returns the denotation of the source chunk.

        Returns:
            str: The denotation of the source chunk in the format "{source}:{start}-{end}".
        """
        return f"{self.source}:{self.start+1}-{self.end+1}"

    def get_xml(self, add_lines: bool = True) -> str:
        """
        Returns the source chunk in XML format.

        Args:
            add_lines (bool): If True, adds line numbers to the chunk in XML.

        Returns:
            str: The source chunk in XML format.
        """
        return f"""<chunk source="{self.denotation}">\n{self.get_chunk_content_with_meta_data(add_lines, add_class_function_info=False)}\n</chunk>"""
