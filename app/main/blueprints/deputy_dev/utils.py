# flake8: noqa
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import set_context_values
from deputydev_core.utils.jwt_handler import JWTHandler
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException

from app.backend_common.constants.constants import VCSTypes
from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.repository.db import DB
from app.backend_common.services.credentials import AuthHandler, AuthHandlerFactory
from app.main.blueprints.deputy_dev.constants.constants import (
    COMBINED_TAGS_LIST,
    BitbucketBots,
)
from app.main.blueprints.deputy_dev.models.dao.postgres import Integrations


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


def get_corrective_code(data):
    corrective_code = data.get("corrective_code")
    if corrective_code:
        corrected_code = corrective_code.replace("\\n", "\n")
        if corrected_code.strip():
            return format_code_block(corrected_code.strip())
    return ""


def format_comment(data: Dict[str, Any] | str | None) -> str:
    # Check if corrective_code exists and is a dictionary
    if isinstance(data, dict):
        comment = data.get("comment", "")
        rationale = data.get("rationale", "")
        corrective_code = get_corrective_code(data)
        bucket_name = get_bucket_name(data)
        if bucket_name:
            return f"**{bucket_name}**: {comment} \n {rationale}\n{corrective_code} "
        else:
            return f"{comment}\n{corrective_code} "
    elif isinstance(data, str):
        return data
    else:
        return ""


def get_bucket_name(data):
    buckets = data.get("buckets")
    if buckets and not data.get("is_summarized"):
        return buckets[0]["name"]
    return ""


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


async def get_workspace_by_team_id(team_id, scm) -> Workspaces:
    workspace = await Workspaces.get(team_id=team_id, scm=scm)
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

    auth_handler = AuthHandlerFactory.create_auth_handler(integration=vcs_type, tokenable_id=tokenable_id)
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

    auth_handler = AuthHandlerFactory.create_auth_handler(integration=client, tokenable_id=int(tokenable_id))
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
        decoded_token = JWTHandler(signing_key=CONFIG.config["WEBHOOK_JWT_SIGNING_KEY"]).verify_token(jwt_token)
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
