# flake8: noqa
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Dict, List, Tuple

from sanic.log import logger
from torpedo import CONFIG
from torpedo.exceptions import BadRequestException

from app.main.blueprints.deputy_dev.constants.constants import (
    COMBINED_TAGS_LIST,
    BitbucketBots,
    PRDiffSizingLabel,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.models.dao import Integrations, Workspaces
from app.main.blueprints.deputy_dev.services.credentials import (
    AuthHandler,
    GithubAuthHandler,
    create_auth_handler,
)
from app.main.blueprints.deputy_dev.services.db.db import DB
from app.main.blueprints.deputy_dev.services.jwt_service import JWTService
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
    set_context_values,
)


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


def ignore_files(pr_diff, excluded_files=None, included_files=None):
    if not excluded_files:
        excluded_files = []
    if not included_files:
        included_files = []
    resp_text = ""
    for d in pr_diff.split("diff --git "):
        if is_any_regex_present(d, included_files) or not is_any_regex_present(d, excluded_files):
            resp_text += d
    return resp_text


def is_path_included(path, excluded_files=None, included_files=None):
    if not excluded_files:
        excluded_files = []
    if not included_files:
        included_files = []
    return is_any_regex_present(path, included_files) or not is_any_regex_present(path, excluded_files)


def is_any_regex_present(text, regex_list):
    for pattern in regex_list:
        if re.search(pattern, text):
            return True
    return False


# def files_to_exclude(exclusions, inclusions, repo_dir=""):
#     """
#     Computes the final list of excluded files or folders after applying inclusions and exclusions.
#
#     :param repo_dir: The root directory path for the repository.
#     :param exclusions: List of paths (relative to repo_dir) to be excluded.
#     :param inclusions: List of paths (relative to repo_dir) to be included even if they are within exclusions.
#     :return: A set of paths (relative to repo_dir) that are effectively excluded.
#     """
#     exclusions = {os.path.join(repo_dir, path) for path in exclusions}
#     inclusions = {os.path.join(repo_dir, path) for path in inclusions}
#
#     final_exclusions = set()
#
#     def is_path_excluded(path, exclusions, inclusions):
#         """
#         Determines if a path should be excluded based on exclusions and inclusions.
#         """
#         for exclusion in exclusions:
#             if os.path.commonpath([path, exclusion]) == exclusion:
#                 for inclusion in inclusions:
#                     if os.path.commonpath([path, inclusion]) == inclusion:
#                         return False
#                 return True
#         return False
#
#     # Process exclusions, filtering out overridden paths
#     for exclusion in exclusions:
#         if not any(os.path.commonpath([exclusion, inclusion]) == inclusion for inclusion in inclusions):
#             final_exclusions.add(exclusion)
#
#     # Add nested files and folders to the final exclusions
#     for exclusion in exclusions:
#         for root, dirs, files in os.walk(exclusion):
#             for item in dirs + files:
#                 full_path = os.path.join(root, item)
#                 if is_path_excluded(full_path, exclusions, inclusions):
#                     final_exclusions.add(full_path)
#
#     # Convert final exclusions to relative paths
#     relative_exclusions = {os.path.relpath(path, repo_dir) for path in final_exclusions}
#
#     return relative_exclusions


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
    buckets = data.get("buckets")
    if buckets and not data.get("is_summarized"):
        return buckets[0]
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


async def get_workspace(scm, scm_workspace_id) -> Workspaces:
    workspace = await Workspaces.get(scm=scm, scm_workspace_id=scm_workspace_id)
    return workspace


async def get_vcs_auth_handler(scm_workspace_id, vcs_type) -> AuthHandler:
    workspace = await get_workspace(scm_workspace_id=scm_workspace_id, scm=vcs_type)
    set_context_values(dd_workspace_id=workspace.id)
    if vcs_type == "github":
        # tokenable_type = "workspace"
        workspace_id = workspace.id
        tokenable_id = workspace_id

    else:
        # tokenable_type = "integration"
        integration_id = workspace.integration_id
        tokenable_id = integration_id

    auth_handler = create_auth_handler(integration=vcs_type, tokenable_id=tokenable_id)
    return auth_handler


async def get_auth_handler(client: str, team_id: str | None = None, workspace_id: str | None = None):
    integration_info = await DB.by_filters(
        model_name=Integrations,
        where_clause={"team_id": team_id, "client": client, "is_connected": True},
        limit=1,
        fetch_one=True,
    )
    if not integration_info:
        return None, None
    if client == "github":
        # tokenable_type = "workspace"
        tokenable_id = workspace_id

    else:
        # tokenable_type = "integration"
        tokenable_id = integration_info["id"]

    auth_handler = create_auth_handler(integration=client, tokenable_id=int(tokenable_id))
    return auth_handler, integration_info


def get_bitbucket_repo_name_slug(value: str) -> str:
    """
    extracts repo slug from the full name passed to it

    Args:
        value (str): string from which the value needs to be extracted.

    Returns:
        datetime: The corresponding datetime object.
    """
    parts = value.split("/")
    return parts[-1]


def is_request_from_blocked_repo(repo_name):
    config = CONFIG.config
    return repo_name in config.get("BLOCKED_REPOS")


def update_payload_with_jwt_data(query_params: dict, payload: dict) -> dict:
    """
    Decodes the JWT token and updates the payload with relevant values.

    Args:
        query_params (dict): query parameters.
        payload (dict): The payload to update with decoded token values.

    Returns:
        dict: Updated payload with the decoded values.
    """
    jwt_token = query_params.get("data")
    if not jwt_token:
        payload = handle_old_request(query_params, payload)
        return payload
    try:
        decoded_token = JWTService.decode(jwt_token)
    except Exception as e:
        raise BadRequestException(f"Invalid JWT token: {e}")

    # Update payload with values from decoded token
    payload["prompt_version"] = decoded_token.get("prompt_version", "v1")
    payload["vcs_type"] = decoded_token.get("vcs_type", VCSTypes.bitbucket.value)
    payload["scm_workspace_id"] = decoded_token.get("scm_workspace_id")

    return payload


def handle_old_request(query_params: dict, payload: dict) -> dict:
    """
    Handles old request where query params only contain vcs_type and prompt version and not a jwt token.

    Args:
        query_params (dict): query parameters.
        payload (dict): The payload to update with decoded token values.

    Returns:
        dict: Updated payload with vcs_type, prompt_version and scm_workspace_id.
    """
    vcs_type = query_params.get("vcs_type", VCSTypes.bitbucket.value)
    prompt_version = query_params.get("prompt_version", "v1")
    payload["vcs_type"] = vcs_type
    payload["prompt_version"] = prompt_version

    # for now only handling for bitbucket and github. Gitlab is not integrated anywhere will always get jwt.
    if vcs_type == VCSTypes.bitbucket.value:
        payload["scm_workspace_id"] = payload["repository"]["workspace"]["uuid"]
    elif vcs_type == VCSTypes.github.value:
        payload["scm_workspace_id"] = payload["organization"]["id"]
    return payload


def create_optimized_batches(texts: List[str], max_tokens: int, model: str) -> List[List[str]]:
    tiktoken_client = TikToken()
    batches = []
    current_batch = []
    currrent_batch_token_count = 0

    for text in texts:
        text_token_count = tiktoken_client.count(text, model=model)

        if text_token_count > max_tokens:  # Single text exceeds max tokens
            truncated_text = tiktoken_client.truncate_string(text=text, max_tokens=max_tokens, model=model)
            batches.append([truncated_text])
            logger.warn(f"Text with token count {text_token_count} exceeds the max token limit of {max_tokens}.")
            continue

        if currrent_batch_token_count + text_token_count > max_tokens:
            batches.append(current_batch)
            current_batch = [text]
            currrent_batch_token_count = text_token_count
        else:
            current_batch.append(text)
            currrent_batch_token_count += text_token_count

    if current_batch:
        batches.append(current_batch)

    return batches


def repo_meta_info_prompt(app_settings):
    language = app_settings.get("language")
    framework = app_settings.get("framework")
    parts = []
    if language:
        parts.append(f"{language}")
    if framework:
        parts.append(f"{framework} framework")

    # Join parts with "with" if both language and framework exist
    prompt = (
        f"The code given to you is using {' with '.join(parts)}. Treat yourself as an expert in these technologies."
        if parts
        else ""
    )
    return prompt


def format_chat_comment_thread_comment(comment):
    """Append comment Start and Comment End in each comment that we add in Comment thread in DD chat flow"""
    return "Comment Start: \n" + comment + "\nComment End \n"
