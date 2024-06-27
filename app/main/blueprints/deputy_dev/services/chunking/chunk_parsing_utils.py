import asyncio
import os
from typing import Generator, List, Set, Tuple

from sanic.log import logger

from app.common.utils.executor import executor
from app.main.blueprints.deputy_dev.services.chunking.chunk_info import ChunkInfo
from app.main.blueprints.deputy_dev.services.chunking.document import (
    Document,
    chunks_to_docs,
)

from .chunk import chunk_source
from .chunk_config import ChunkConfig


def get_absolute_path(file_path: str, visited: Set[str]) -> Generator[str, None, None]:
    """
    Recursively traverses the directory structure starting from the given file path.

    Args:
        file_path (str): The path to the directory or file to start traversal from.
        directory (str): The root directory from which traversal begins.
        visited (Set[str]): A set to store visited file paths to avoid revisiting them.

    Yields:
        str: The absolute file paths found during traversal.

    Note:
        Directories named 'node_modules', '.venv', 'build', 'venv', or 'patch' are ignored.
    """
    only_file_name = os.path.basename(file_path)
    if only_file_name in ("node_modules", ".venv", "build", "venv", "patch"):
        return
    if file_path in visited:
        return
    visited.add(file_path)
    if os.path.isdir(file_path):
        for file_name in os.listdir(file_path):
            for sub_file_path in get_absolute_path(os.path.join(file_path, file_name), visited):
                yield sub_file_path
    else:
        yield file_path


def read_file_with_fallback_encodings(source: str) -> str:
    """
    Reads the content of a file with utf-8 encoding.

    Args:
        source (str): The path to the file to be read.

    Returns:
        str: The content of the file.

    Raises:
        UnicodeDecodeError: If the file cannot be decoded with utf-8 encoding.
    """

    try:
        with open(source, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        logger.error(f"Could not decode {source} with utf-8 encoding")


def filter_file(directory: str, file: str, chunk_config: ChunkConfig) -> bool:
    """
    Check if a file should be filtered based on its size and other criteria.

    Args:
        file (str): The path to the file.
        chunk_config (ChunkConfig): The configuration object.

    Returns:
        bool: True if the file should be included, False otherwise.
    """
    for ext in chunk_config.exclude_exts:
        if file.endswith(ext):
            return False
    for dir_name in chunk_config.exclude_dirs:
        if file[len(directory) + 1 :].startswith(dir_name):
            return False

    # Removing file size check since we are chunking files
    # try:
    #     if os.stat(file).st_size > ChunkFileSizeLimit.MAX.value:
    #         return False
    #     if os.stat(file).st_size < ChunkFileSizeLimit.MIN.value:
    #         return False
    # except FileNotFoundError as e:
    #     logger.error(f"File not found: {file}. Error: {e}")
    #     return False
    if not os.path.isfile(file):
        return False
    try:
        # fetch file
        read_file_with_fallback_encodings(file)
    except UnicodeDecodeError:
        logger.warning(f"UnicodeDecodeError: {file}, skipping")
        return False
    return True


def is_dir_too_big(file_name: str, file_threshold: int = 240) -> bool:
    """
    Checks if the directory containing the given file has more files than a specified threshold.

    Args:
        file_name (str): The path to a file within the directory to check.
        file_threshold (int, optional): The maximum number of files allowed in the directory. Defaults to 240.

    Returns:
        bool: True if the directory is considered too big, False otherwise.
    """
    dir_file_count = {}
    dir_name = os.path.dirname(file_name)
    if dir_name not in dir_file_count:
        dir_file_count[dir_name] = len(os.listdir(dir_name))
    return dir_file_count[dir_name] > file_threshold


def read_file(file_name: str) -> str:
    """
    Reads the content of a file.

    Args:
        file_name (str): The path to the file to be read.

    Returns:
        str: The content of the file.

    Raises:
        SystemExit: If the file cannot be read due to a SystemExit exception.
    """
    try:
        with open(file_name, "r") as f:
            return f.read()
    except SystemExit:
        raise SystemExit
    except Exception:
        return ""


def create_chunks(source: str) -> list[str]:
    """
    Converts the content of a file into chunks of code.

    Args:
        source (str): The path to the file to be processed.

    Returns:
        list[str]: A list of code chunks extracted from the file.
    """
    file_contents = read_file(source)
    chunks = chunk_source(file_contents, path=source)
    return chunks


def source_to_chunks(directory: str, config: ChunkConfig = None) -> tuple[list[ChunkInfo], list[Document]]:
    """
    Converts code files within a directory into chunks of code.

    Args:
        directory (str): The path to the directory containing code files.
        config (ChunkConfig, optional): Configuration for chunking. Defaults to None.

    Returns:
        tuple[list[ChunkInfo], list[Document]]: A tuple containing a list of chunk information and a list of docs.
    """
    # If no configuration provided, use default ChunkConfig
    chunk_config = config if config else ChunkConfig()

    # Initialize a set to track visited directories
    visited = set()

    # Get list of absolute file paths within the directory
    file_list = get_absolute_path(directory, visited)

    # Filter the file list based on ChunkConfig and other conditions
    file_list = [
        file_name
        for file_name in file_list
        if filter_file(directory, file_name, chunk_config)
        and os.path.isfile(file_name)  # Ensure it's a file
        and not is_dir_too_big(file_name)  # Ensure file size is not too big
    ]

    # Initialize an empty list to store all code chunks
    all_chunks = []

    # Iterate over each file and create chunks
    for file in file_list:
        all_chunks.extend(create_chunks(file))

    # Convert chunks to Document objects
    all_docs: List[Document] = chunks_to_docs(all_chunks, len(directory) + 1)

    # Adjust source paths in chunks to be relative to the directory
    for chunk in all_chunks:
        chunk.source = chunk.source[len(directory) + 1 :]

    # Return both the list of chunk information and the list of file paths
    return all_chunks, all_docs


async def get_chunks(directory: str) -> Tuple[List[ChunkInfo], List[Document]]:
    """
    Asynchronously retrieves chunks and documents from a given directory.

    This function uses a ProcessPoolExecutor to offload the chunk retrieval process
    to a separate process, thus avoiding blocking the main event loop.

    Args:
        directory (str): The directory from which to retrieve chunks and documents.

    Returns:
        Tuple[List[ChunkInfo], List[Document]]: A tuple containing two lists:
            - A list of ChunkInfo objects.
            - A list of Document objects.
    """
    # Instantiate an event loop object for main thread
    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(executor, source_to_chunks, directory)
    all_chunks = result[0]
    all_docs = result[1]
    return all_chunks, all_docs


def render_snippet_array(chunks):
    joined_chunks = "\n".join([chunk.get_xml(add_lines=False) for chunk in chunks])
    start_chunk_tag = "<relevant_chunks_in_repo>"
    end_chunk_tag = "</relevant_chunks_in_repo>"
    if joined_chunks.strip() == "":
        return ""
    return start_chunk_tag + "\n" + joined_chunks + "\n" + end_chunk_tag
