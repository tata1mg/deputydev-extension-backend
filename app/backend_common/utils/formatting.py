import re
from enum import Enum

from app.backend_common.constants.constants import (
    PR_SIZING_TEXT,
    PR_SUMMARY_COMMIT_TEXT,
    PR_SUMMARY_TEXT,
)


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


def categorize_loc(loc: int) -> tuple:
    """
    Categorizes the number of lines of code (LOC) into predefined size categories.

    Args:
        loc (int): The total number of lines of code.

    Returns:
        str: The size category based on the number of lines of code.
            - "XS" for 0-9 lines
            - "S" for 10-29 lines
            - "M" for 30-99 lines
            - "L" for 100-499 lines
            - "XL" for 500-999 lines
            - "XXL" for 1000+ lines
    """
    if loc < 10:
        return PRDiffSizingLabel.XS.value, PRDiffSizingLabel.XS_TIME.value
    elif loc < 30:
        return PRDiffSizingLabel.S.value, PRDiffSizingLabel.S_TIME.value
    elif loc < 100:
        return PRDiffSizingLabel.M.value, PRDiffSizingLabel.M_TIME.value
    elif loc < 500:
        return PRDiffSizingLabel.L.value, PRDiffSizingLabel.L_TIME.value
    elif loc < 1000:
        return PRDiffSizingLabel.XL.value, PRDiffSizingLabel.XL_TIME.value
    else:
        return PRDiffSizingLabel.XXL.value, PRDiffSizingLabel.XXL_TIME.value


def format_summary_with_metadata(summary: str, loc: int, commit_id: str) -> str:
    """Format the summary with PR metadata including size, LOC, and commit info."""
    category, time = categorize_loc(loc)
    loc_text, time_text = format_summary_loc_time_text(loc, category, time)

    # Format the complete summary with metadata
    formatted_summary = (
        f"\n\n---\n\n{PR_SUMMARY_TEXT}"
        f"\n\n---\n\n{PR_SIZING_TEXT.format(category=category, loc=loc_text, time=time_text)}"
        f"\n\n---\n\n{summary}"
        f"\n\n---\n\n{PR_SUMMARY_COMMIT_TEXT.format(commit_id=commit_id)}"
    )

    return formatted_summary


def append_line_numbers(pr_diff: str) -> str:  # noqa: C901
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

    if not result:
        return pr_diff

    return "\n".join(result)
