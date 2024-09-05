# flake8: noqa
import re
from datetime import datetime
from typing import Dict, List, Tuple

from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import (
    COMBINED_TAGS_LIST,
    IGNORE_FILES,
    BitbucketBots,
    PRDiffSizingLabel,
)
from app.main.blueprints.deputy_dev.loggers import AppLogger


def remove_special_char(char, input_string):
    return input_string.replace(char, "")


def get_comment(payload):
    try:
        bb_payload = {}
        comment = payload["comment"]
        raw_content = remove_special_char("\\", comment["content"]["raw"])
        if "parent" in comment and "inline" in comment:
            bb_payload["comment"] = raw_content
            bb_payload["parent"] = comment["parent"]["id"]
            bb_payload["path"] = comment["inline"]["path"]
            return bb_payload
        elif "inline" in comment:
            bb_payload["comment"] = raw_content
            bb_payload["path"] = comment["inline"]["path"]
            bb_payload["line_number"] = comment["inline"]["to"]
            return bb_payload
        else:
            return {"comment": raw_content}
    except KeyError as e:
        raise f"Error: {e} not found in the JSON structure."
    except Exception as e:
        raise f"An unexpected error occurred: {e}"


def add_corrective_code(data):
    # Check if corrective_code exists and is a dictionary
    if isinstance(data, dict):
        comment = data.get("comment", "")
        if data.get("corrective_code") and len(data.get("corrective_code")) > 0:
            comment += "\n" + format_code_block(data.get("corrective_code"))
        return comment
    elif isinstance(data, str):
        return data
    else:
        return ""


def format_code_block(code_block: str) -> str:
    """
    Formats a code block into the correct format by enclosing it with triple backticks if not already enclosed.

    Parameters:
    code_block (str): The input code block as a string.

    Returns:
    str: The formatted code block.
    """
    if not (code_block.startswith("```") and code_block.endswith("```")):
        # Add triple backticks around the code block if its not formatted
        return f"```\n{code_block}\n```"
    return code_block


def ignore_files(response):
    resp_text = ""
    for d in response.text.split("diff --git "):
        if not any(keyword in d for keyword in IGNORE_FILES):
            resp_text += d
    return resp_text


def get_filtered_response(response: dict, confidence_filter_score: float) -> bool:
    """
    Filters the response based on the given confidence filter score.

    Args:
        response (Dict[str, Any]): The response dictionary containing a confidence score.
        confidence_filter_score (float): The threshold confidence score for filtering.

    Returns:
        bool: whether the response passes check or not.

    """
    confidence_score = response.get("confidence_score")
    return response.get("comment") and float(confidence_score) >= float(confidence_filter_score)


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


def parse_collection_name(name: str) -> str:
    # Replace any non-alphanumeric characters with hyphens
    name = re.sub(r"[^\w-]", "--", name)
    # Ensure the name is between 3 and 63 characters and starts/ends with alphanumeric
    name = re.sub(r"^(-*\w{0,61}\w)-*$", r"\1", name[:63].ljust(3, "x"))
    return name


def get_corrective_code(data):
    corrective_code = data.get("corrective_code")
    if corrective_code:
        corrected_code = corrective_code.replace("\\n", "\n")
        if corrected_code.strip():
            return format_code_block(corrected_code.strip())
    return ""


def format_comment(data):
    # Check if corrective_code exists and is a dictionary
    if isinstance(data, dict):
        comment = data.get("comment", "")
        corrective_code = get_corrective_code(data)
        bucket_name = get_bucket_name(data)
        if bucket_name:
            return f"**{bucket_name}**: {comment}\n{corrective_code} "
        else:
            return f"{comment}\n{corrective_code} "
    elif isinstance(data, str):
        return data
    else:
        return ""


def get_bucket_name(data):
    bucket_name = data.get("bucket")
    if bucket_name:
        return bucket_name
    return ""


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
                result.append(f"<+{new_line_number}>{line}")
            new_line_number += 1
            continue

        # Handle removed lines
        if line.startswith("-") and not line.startswith("---"):
            if current_file:
                result.append(f"<-{original_line_number}>{line}")
            original_line_number += 1
            continue

        # Handle unchanged lines
        if not line.startswith("-") and not line.startswith("+") and not line.startswith("@@"):
            if current_file:
                result.append(f"<+{new_line_number}>{line}")
            new_line_number += 1
            original_line_number += 1

    return "\n".join(result)


def get_foundation_model_name():
    model_config = CONFIG.config.get("SCRIT_MODEL")
    model = model_config["MODEL"]
    return model


def get_approval_time_from_participants_bitbucket(participants):
    if not participants:
        return
    participants = [participant for participant in participants if participant["participated_on"]]
    if not participants:
        return
    sorted_participants = sorted(participants, key=lambda x: datetime.fromisoformat(x["participated_on"]))
    for participant in sorted_participants:
        if participant["approved"] is True and participant["state"] == "approved":
            return participant["participated_on"]


def is_human_comment(actor, comment_raw):
    human_comment = False
    if actor not in BitbucketBots.list():
        human_comment = not any(comment_raw.lower().startswith(f"{tag}") for tag in COMBINED_TAGS_LIST)
    return human_comment


def count_bot_and_human_comments_bitbucket(comments: List[Dict]) -> Tuple[int, int]:
    """
    Count the number of comments made by the bot and others.

    Args:
        comments (List[Dict]): List of comments from Bitbucket.

    Returns:
        Tuple[int, int]: Tuple containing two integers - count of bot comments and count of other comments.
    """
    chat_authors = BitbucketBots.list()
    bot_comment_count = 0
    human_comment_count = 0
    for comment in comments:
        if comment.get("parent") is None:
            if comment.get("user", {}).get("display_name") in chat_authors:
                # There are many bots that are currently running in bitbucket, but we are only considering
                # the comment from DeputyDev for llm count, rest of the bot comment counts are ignored
                if comment.get("user", {}).get("display_name") == BitbucketBots.DEPUTY_DEV.value:
                    bot_comment_count += 1
            else:
                # Any tags such as #scrit, #like or any other whitelisted tags we receive starts with
                # \#dd, \#scrit, that is why we are filtering out this tags starting with "\"
                comment_raw = comment.get("content").get("raw")
                if not any(comment_raw.lower().startswith(f"\{tag}") for tag in COMBINED_TAGS_LIST):
                    human_comment_count += 1

    return bot_comment_count, human_comment_count


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


def format_summary_loc_time_text(loc: int, category: str, time: str) -> tuple:
    if category == PRDiffSizingLabel.XXL.value:
        return "1000+", f"{time} to review, potentially spread across multiple sessions"
    return str(loc), f"{time} to review"


def extract_line_number_from_llm_response(line_number: str):

    if not isinstance(line_number, str):
        AppLogger.log_warn("Invalid line number for comment: {}".format(line_number))
        return

    line_number = line_number.strip()
    if line_number.lower() == "n/a":
        AppLogger.log_warn("Invalid line number for comment: {}".format(line_number))
        return  # global comment

    match = re.search(r"-?\d+", line_number)
    #  Handles following cases:
    #  "+21, +22", "21, 22", "21-22", "-21", "-21, -23", "22"
    if match:
        line_number_int = int(match.group())

        # return 1 if the line number is 0
        if line_number_int == 0:
            return 1

        return line_number_int

    AppLogger.log_warn("Invalid line number for comment: {}".format(line_number))
    return  # global comment
