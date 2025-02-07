import re
from typing import Dict, Tuple, List


def get_response_code_lines(response: str):
    """
    Extracts number lines of code from the LLM response where we have code content in backticks ```.

    :param response: The LLM response containing code blocks in triple backticks.
    :return: Total number of code lines.
    """

    # Find all code blocks inside triple backticks
    code_blocks = re.findall(r"```[a-zA-Z0-9]*\n(.*?)```", response, re.DOTALL)

    total_code_lines = sum(len(block.splitlines()) for block in code_blocks)

    return total_code_lines


def get_chunks_by_file_total_lines(chunks_by_file: Dict[str, List[Tuple[int, int, str]]]) -> int:
    total_lines = 0

    for chunks in chunks_by_file.values():
        for _, _, content in chunks: # chunk = (1,22, "\n def a(): \n pass")
            cleaned_content = content.lstrip("\n")  # Remove initial new line
            total_lines += cleaned_content.count("\n")

    return total_lines
