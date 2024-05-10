import re
import traceback
from dataclasses import dataclass
from typing import Union

import tree_sitter_javascript
from sanic.log import logger
from tree_sitter import Language, Node, Parser
from tree_sitter_languages import get_parser as tree_sitter_get_parser

from app.constants.chunking import CHARACTER_SIZE, EXTENSION_TO_LANGUAGE

from .chunk_info import ChunkInfo


def get_parser(language: str) -> Parser:
    """
    Returns a parser for the specified language.

    Args:
        language (str): The name of the language.

    Returns:
        Parser: A parser object for the specified language.
    """
    parser = Parser()
    if language == "javascript":
        lang = Language(tree_sitter_javascript.language(), "javascript")
    else:
        return tree_sitter_get_parser(language)

    parser.set_language(lang)
    return parser


def get_line_number(index: int, source_code: str) -> int:
    """
    Gets the line number corresponding to a given character index in the source code.

    Args:
        index (int): The character index.
        source_code (str): The source code string.

    Returns:
        int: The line number (1-indexed) where the character index is located.

    Example:
        >>> code = "def hello():\n    print('Hello, world!')"
        >>> get_line_number(13, code)
        2
    """
    total_chars = 0
    line_number = 0
    for line_number, line in enumerate(source_code.splitlines(keepends=True), start=1):
        total_chars += len(line)
        if total_chars > index:
            return line_number
    return line_number


def non_whitespace_len(s: str) -> int:
    """
    Calculates the length of a string excluding whitespace characters.

    Args:
        s (str): The input string.

    Returns:
        int: The length of the string excluding whitespace characters.
    """
    return len(re.sub("\s", "", s))


@dataclass
class Span:
    """
    Represents a slice of a string.

    Attributes:
        start (int): The starting index of the span.
        end (int): The ending index of the span.
    """

    start: int = 0
    end: int = 0

    def __post_init__(self):
        """
        If end is None, set it to start.
        """
        if self.end is None:
            self.end = self.start

    def extract(self, s: str) -> str:
        """
        Extracts the corresponding substring of string s.

        Args:
            s (str): The input string.

        Returns:
            str: The extracted substring.
        """
        return s[self.start : self.end]

    def extract_lines(self, s: str) -> str:
        """
        Extracts the corresponding substring of string s by lines.

        Args:
            s (str): The input string.

        Returns:
            str: The extracted substring.
        """
        return "\n".join(s.splitlines()[self.start : self.end + 1])

    def __add__(self, other: Union["Span", int]) -> "Span":
        """
        Concatenates two spans or adds an integer to the span.

        Args:
            other (Union[Span, int]): The other span to concatenate or the integer to add.

        Returns:
            Span: The concatenated span.

        Raises:
            NotImplementedError: If the type of 'other' is not supported.
        """
        if isinstance(other, int):
            return Span(self.start + other, self.end + other)
        elif isinstance(other, Span):
            return Span(self.start, other.end)
        else:
            raise NotImplementedError("Unsupported type for 'other'. Must be Span or int.")

    def __len__(self) -> int:
        """
        Computes the length of the span.

        Returns:
            int: The length of the span.
        """
        return self.end - self.start


def chunk_tree(
    tree,
    source_code: bytes,
    MAX_CHARS=CHARACTER_SIZE,
    coalesce=100,
) -> list["Span"]:
    """
    Chunk the AST tree based on maximum characters and coalesce size.

    Args:
        tree: The AST tree.
        source_code (bytes): The source code bytes.
        MAX_CHARS (int): Maximum characters per chunk.
        coalesce (int): Coalesce size.

    Returns:
        list[Span]: List of chunks.
    """

    # 1. Recursively form chunks
    def chunk_node(node: Node) -> list[Span]:
        chunks: list[Span] = []
        current_chunk: Span = Span(node.start_byte, node.start_byte)
        node_children = node.children
        for child in node_children:
            if child.end_byte - child.start_byte > MAX_CHARS:
                chunks.append(current_chunk)
                current_chunk = Span(child.end_byte, child.end_byte)
                chunks.extend(chunk_node(child))
            elif child.end_byte - child.start_byte + len(current_chunk) > MAX_CHARS:
                chunks.append(current_chunk)
                current_chunk = Span(child.start_byte, child.end_byte)
            else:
                current_chunk += Span(child.start_byte, child.end_byte)
        chunks.append(current_chunk)
        return chunks

    chunks = chunk_node(tree.root_node)

    # 2. Filling in the gaps
    if len(chunks) == 0:
        return []
    if len(chunks) < 2:
        end = get_line_number(chunks[0].end, source_code)
        return [Span(0, end)]
    for i in range(len(chunks) - 1):
        chunks[i].end = chunks[i + 1].start
    chunks[-1].end = tree.root_node.end_byte

    # 3. Combining small chunks with bigger ones
    new_chunks = []
    current_chunk = Span(0, 0)
    for chunk in chunks:
        current_chunk += chunk
        # if the current chunk starts with a closing parenthesis, bracket, or brace, we coalesce it with the previous chunk
        stripped_contents = current_chunk.extract(source_code.decode("utf-8")).strip()
        first_char = stripped_contents[0] if stripped_contents else ""
        if first_char in [")", "}", "]"] and new_chunks:
            new_chunks[-1] += chunk
            current_chunk = Span(chunk.end, chunk.end)
        # if the current chunk is too large, create a new chunk, otherwise, combine the chunks
        elif non_whitespace_len(
            current_chunk.extract(source_code.decode("utf-8"))
        ) > coalesce and "\n" in current_chunk.extract(source_code.decode("utf-8")):
            new_chunks.append(current_chunk)
            current_chunk = Span(chunk.end, chunk.end)
    if len(current_chunk) > 0:
        new_chunks.append(current_chunk)

    # 4. Changing line numbers
    first_chunk = new_chunks[0]
    line_chunks = [Span(0, get_line_number(first_chunk.end, source_code))]
    for chunk in new_chunks[1:]:
        start_line = get_line_number(chunk.start, source_code) + 1
        end_line = get_line_number(chunk.end, source_code)
        line_chunks.append(Span(start_line, max(start_line, end_line)))

    # 5. Eliminating empty chunks
    line_chunks = [chunk for chunk in line_chunks if len(chunk) > 0]

    # 6. Coalescing last chunk if it's too small
    if len(line_chunks) > 1 and len(line_chunks[-1]) < coalesce:
        line_chunks[-2] += line_chunks[-1]
        line_chunks.pop()

    return line_chunks


def naive_chunker(code: str, line_count: int = 30, overlap: int = 15):
    """
    Naive chunking of code based on line count and overlap.

    Args:
        code (str): The source code string.
        line_count (int): Number of lines per chunk.
        overlap (int): Overlap between chunks.

    Returns:
        List[str]: List of chunks.
    """
    if overlap >= line_count:
        raise ValueError("Overlap should be smaller than line_count.")
    lines = code.split("\n")
    total_lines = len(lines)
    chunks = []

    start = 0
    while start < total_lines:
        end = min(start + line_count, total_lines)
        chunk = "\n".join(lines[start:end])
        chunks.append(chunk)
        start += line_count - overlap

    return chunks


def chunk_source(
    content: str,
    path: str,
    MAX_CHARS=CHARACTER_SIZE,
    coalesce=80,
) -> list[ChunkInfo]:
    """
    Chunk the given content into smaller segments.

    Args:
        content (str): The content to be chunked.
        path (str): The file path of the content.
        MAX_CHARS (int, optional): Maximum characters per chunk. Defaults to 1200.
        coalesce (int, optional): Coalesce parameter for chunking. Defaults to 80.

    Returns:
        List[ChunkInfo]: A list of ChunkInfo objects representing the chunks of content.
    """
    ext = path.split(".")[-1]
    if ext in EXTENSION_TO_LANGUAGE:
        language = EXTENSION_TO_LANGUAGE[ext]
    else:
        # Fallback to naive chunking if tree_sitter fails
        line_count = 50
        overlap = 0
        get_chunks = naive_chunker(content, line_count, overlap)
        chunks = []
        for idx, chunk in enumerate(get_chunks):
            end = min((idx + 1) * (line_count - overlap), len(content.split("\n")))
            new_snippet = ChunkInfo(
                content=content,
                start=idx * (line_count - overlap),
                end=end,
                source=path,
            )
            chunks.append(new_snippet)
        return chunks
    try:
        parser = get_parser(language)
        tree = parser.parse(content.encode("utf-8"))
        get_chunks = chunk_tree(tree, content.encode("utf-8"), MAX_CHARS=MAX_CHARS, coalesce=coalesce)
        chunks = []
        for chunk in get_chunks:
            new_snippet = ChunkInfo(
                content=content,
                start=chunk.start,
                end=chunk.end,
                source=path,
            )
            chunks.append(new_snippet)
        return chunks
    except Exception:
        logger.error(traceback.format_exc())
        return []
