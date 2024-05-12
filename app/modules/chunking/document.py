from dataclasses import dataclass
from typing import List

from .chunk_info import ChunkInfo


@dataclass
class Document:
    """
    Data class representing a document.

    Attributes:
        title (str): The title of the document.
        content (str): The content of the document.
    """

    title: str
    content: str


def chunks_to_docs(chunks: List[ChunkInfo], len_dir: int) -> List[Document]:
    """
    Convert a list of ChunkInfo objects to a list of Document objects.

    Args:
        chunks (List[ChunkInfo]): List of ChunkInfo objects representing document chunks.
        len_dir (int): Length of the directory path.

    Returns:
        List[Document]: List of Document objects.
    """
    docs: List[Document] = []
    for chunk in chunks:
        docs.append(
            Document(
                title=f"{chunk.source[len_dir:]}:{chunk.start}-{chunk.end}",
                content=chunk.get_snippet(add_ellipsis=False, add_lines=False),
            )
        )
    return docs
