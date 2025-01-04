import re
from enum import Enum


def format_code_blocks(comment: str) -> str:
    """
    Replace all occurrences of the pattern with triple backticks without preceding spaces and added a \n before ```
    Args:
        comment (string): Comment provided by llm

    Returns:
      string: formatted_comment without triple backticks without preceding spaces
    """
    pattern = re.compile(r"\s*```")

    formatted_comment = pattern.sub("\n```", comment)

    return formatted_comment


def format_comment_bucket_name(input_string: str) -> str:
    """
    Convert a given string to uppercase and replace spaces with underscores,
    preparing it for storage as a CITEXT field in a database.
    Args:
        input_string (str): The string to be converted.
    Returns:
        str: The converted string in uppercase with spaces replaced by underscores.

    Example:
        >>> convert_to_ci_text_field("runtime error")
        'RUNTIME_ERROR'
    """
    # Convert the input string to uppercase
    uppercase_string = input_string.upper()
    # Replace spaces with underscores
    ci_text_field = uppercase_string.replace(" ", "_")
    return ci_text_field


class PRDiffSizingLabel(Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XS_TIME = "5-15 minutes"
    S_TIME = "15-30 minutes"
    M_TIME = "30-60 minutes"
    L_TIME = "1-3 hours"
    XL_TIME = "3-6 hours"
    XXL_TIME = "6+ hours"


def format_summary_loc_time_text(loc: int, category: str, time: str) -> tuple:
    if category == PRDiffSizingLabel.XXL.value:
        return "1000+", f"{time} to review, potentially spread across multiple sessions"
    return str(loc), f"{time} to review"


def append_line_numbers(pr_diff: str) -> str:
    """Append line numbers to PR diff
    Args:
        pr_diff (str): pr diff returned from git diff
    Returns:
        str: pr_diff with line number
    """

    result = []
    current_file = None
    original_line_number = 0
    new_line_number = 0

    lines = pr_diff.split("\n")
    for line in lines:
        # Match the start of a new file diff
        file_match = re.match(r"^\+\+\+ b/(.+)$", line)
        if file_match:
            current_file = file_match.group(1)
            result.append(line)
            continue

        # Match the line number info
        line_info_match = re.match(r"^@@ -(\d+),\d+ \+(\d+),\d+ @@", line)
        if line_info_match:
            original_line_number = int(line_info_match.group(1))
            new_line_number = int(line_info_match.group(2))
            result.append(line)
            continue

        # Handle added lines
        if line.startswith("+") and not line.startswith("+++"):
            if current_file:
                result.append(f"<+{new_line_number}> {line}")
            new_line_number += 1
            continue

        # Handle removed lines
        if line.startswith("-") and not line.startswith("---"):
            if current_file:
                result.append(f"<-{original_line_number}> {line}")
            original_line_number += 1
            continue

        # Handle unchanged lines
        if not line.startswith("-") and not line.startswith("+") and not line.startswith("@@"):
            if current_file:
                result.append(f"<+{new_line_number}> {line}")
            new_line_number += 1
            original_line_number += 1

    return "\n".join(result)
