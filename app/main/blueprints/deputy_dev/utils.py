import re

from app.main.blueprints.deputy_dev.constants.constants import IGNORE_FILES


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


def parse_collection_name(name: str) -> str:
    # Replace any non-alphanumeric characters with hyphens
    name = re.sub(r"[^\w-]", "--", name)
    # Ensure the name is between 3 and 63 characters and starts/ends with alphanumeric
    name = re.sub(r"^(-*\w{0,61}\w)-*$", r"\1", name[:63].ljust(3, "x"))
    return name


def get_corrective_code(data):
    if data.get("corrective_code") and len(data.get("corrective_code")) > 0:
        format_code_block(data.get("corrective_code"))
        return format_code_block(data.get("corrective_code"))
    return ""


def format_comment(data):
    # Check if corrective_code exists and is a dictionary
    if isinstance(data, dict):
        comment = data.get("comment")
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
    bucket_name = data.get("bucket_name")
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
