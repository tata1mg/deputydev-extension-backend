import multiprocessing
import os
from typing import Generator, List, Optional, Set

from sanic.log import logger
from tqdm import tqdm

from app.modules.chunking.chunk_info import ChunkInfo

from .chunk import chunk_source
from .chunk_config import ChunkConfig


def dfs(file_path: str, visited: Set[str]) -> Generator[str, None, None]:
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
            for sub_file_path in dfs(os.path.join(file_path, file_name), visited):
                yield sub_file_path
    else:
        yield file_path


def read_file_with_fallback_encodings(source: str, encodings: Optional[List[str]] = None) -> str:
    """
    Reads the content of a file with fallback encodings if the default encoding fails.

    Args:
        source (str): The path to the file to be read.
        encodings (List[str], optional): List of encodings to try. Defaults to ["utf-8", "windows-1252", "iso-8859-1"].

    Returns:
        str: The content of the file.

    Raises:
        UnicodeDecodeError: If the file cannot be decoded with any of the specified encodings.
    """
    if encodings is None:
        encodings = ["utf-8", "windows-1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            with open(source, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(f"Could not decode {source} with any of the specified encodings: {encodings}")


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
    try:
        if os.stat(file).st_size > 240000:
            return False
        if os.stat(file).st_size < 10:
            return False
    except FileNotFoundError as e:
        logger.error(f"File not found: {file}. Error: {e}")
        return False
    if not os.path.isfile(file):
        return False
    with open(file, "rb") as f:
        is_binary = False
        for block in iter(lambda: f.read(1024), b""):
            if b"\0" in block:
                is_binary = True
                break
        if is_binary:
            return False
        f.close()
    try:
        # fetch file
        data = read_file_with_fallback_encodings(file)
        lines = data.split("\n")
    except UnicodeDecodeError:
        logger.warning(f"UnicodeDecodeError: {file}, skipping")
        return False
    line_count = len(lines)
    # if average line length is greater than 200, then it is likely not human readable
    if len(data) / line_count > 200:
        return False
    # # check token density, if it is greater than 2, then it is likely not human readable
    # token_count = tiktoken_client.count(data)
    # if token_count == 0:
    #     return False
    # if len(data)/token_count < 2:
    #     return False
    return True


def is_dir_too_big(file_name: str, file_threshold: int = 240) -> bool:
    """
    Checks if the directory containing the given file has more files than a specified threshold.

    Args:
        file_name (str): The path to a file within the directory to check.
        file_threshold (int, optional): The maximum number of files allowed in the directory. Defaults to 240.

    Returns:
        bool: True if the directory is considered too big, False otherwise.

    Note:
        Directories named 'node_modules', '.venv', 'build', 'venv', or 'patch' are considered too big.
    """
    dir_file_count = {}
    dir_name = os.path.dirname(file_name)
    only_file_name = os.path.basename(dir_name)
    if only_file_name in ("node_modules", ".venv", "build", "venv", "patch"):
        return True
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


def source_to_chunks(directory: str, config: ChunkConfig = None) -> tuple[list[ChunkInfo], list[str]]:
    """
    Converts code files within a directory into chunks of code.

    Args:
        directory (str): The path to the directory containing code files.
        config (ChunkConfig, optional): Configuration for chunking. Defaults to None.

    Returns:
        tuple[list[ChunkInfo], list[str]]: A tuple containing a list of chunk information and a list of file paths.
    """
    chunk_config = config if config else ChunkConfig()
    logger.info(f"Reading files from {directory}")
    visited = set()
    file_list = dfs(directory, visited)
    file_list = [
        file_name
        for file_name in file_list
        if filter_file(directory, file_name, chunk_config)
        and os.path.isfile(file_name)
        and not is_dir_too_big(file_name)
    ]
    logger.info("Done reading files")
    all_chunks = []
    with multiprocessing.Pool(processes=multiprocessing.cpu_count() // 4) as pool:
        for chunks in tqdm(pool.imap(create_chunks, file_list), total=len(file_list)):
            all_chunks.extend(chunks)
    return all_chunks, file_list
