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

    def get_snippet(self, add_ellipsis: bool = True, add_lines: bool = True):
        """
        Get a snippet of the chunk.

        Args:
            add_ellipsis (bool, optional): Whether to add ellipsis (...) at the beginning and end of the snippet. Defaults to True.
            add_lines (bool, optional): Whether to prepend line numbers to each line of the snippet. Defaults to True.

        Returns:
            str: The snippet of the chunk.
        """
        lines = self.content.splitlines()
        snippet = "\n".join(
            (f"{i + self.start}: {line}" if add_lines else line)
            for i, line in enumerate(lines[max(self.start - 1, 0): self.end])
        )
        if add_ellipsis:
            if self.start > 1:
                snippet = "...\n" + snippet
            if self.end < self.content.count("\n") + 1:
                snippet = snippet + "\n..."
        return snippet

    @property
    def denotation(self):
        return f"{self.source}:{self.start}-{self.end}"
