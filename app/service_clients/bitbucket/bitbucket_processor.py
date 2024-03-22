import logging
import re
from datetime import datetime

import requests
from torpedo import CONFIG

from app.constants.constants import COMMENTS_DEPTH
from app.utils import add_corrective_code, ignore_files

config = CONFIG.config

URL = config.get("BITBUCKET_URL")
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": config.get("BITBUCKET_KEY"),
}

# TODO - This file should ideally be in service_client. This file is a service client for bitbucket.
#  Extract as much logic as you can from this into manager files and move this to service_clients package.


class BitbucketProcessor:
    def __init__(self):
        pass

    @staticmethod
    async def get_pr_details(payload):
        diff_url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}"
        response = requests.get(
            diff_url,
            headers=HEADERS,
        ).json()
        if not response:
            raise ValueError("Invalid PR.")

        created_time = datetime.fromisoformat(response["created_on"][:-6])
        updated_time = datetime.fromisoformat(response["updated_on"][:-6])

        # Calculate the time difference in minutes
        time_difference = (updated_time - created_time).total_seconds() / 60
        if time_difference > 5:
            return {"created": False, "title": response["title"], "description": response["description"]}
        else:
            return {"created": True, "title": response["title"], "description": response["description"]}

    @staticmethod
    async def create_comment_on_line(payload, comment: dict):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        comment_payload = {
            "content": {"raw": add_corrective_code(comment)},
            "inline": {
                "path": comment.get("file_path")[2:]
                if re.match(r"^[ab]", comment.get("file_path"))
                else comment.get("file_path"),
                "to": comment.get("line_number"),
            },
        }
        response = requests.post(url, headers=HEADERS, json=comment_payload)
        return response.json()

    @staticmethod
    async def create_comment_on_comment(payload, comment, comment_payload):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        # TODO - Will this be able to add code blocks as part of comments?
        comment_payload = {
            "content": {"raw": add_corrective_code(comment)},
            "parent": {"id": comment_payload["parent"]},
            "inline": {"path": comment_payload["path"]},
        }
        response = requests.post(url, headers=HEADERS, json=comment_payload)
        return response.json()

    @staticmethod
    async def create_comment_on_pr(payload, comment):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        comment_payload = {"content": {"raw": comment}}
        response = requests.post(url, headers=HEADERS, json=comment_payload)
        return response.json()

    @staticmethod
    async def get_pr_diff(payload):
        diff_url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/diff"
        response = requests.get(
            diff_url,
            headers=HEADERS,
        )
        return ignore_files(response)

    @staticmethod
    async def fetch_comment_thread(payload, comment_id, depth=0):
        try:
            if depth >= COMMENTS_DEPTH:
                return ""  # Stop recursion when depth exceeds 7
            api_url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments/{comment_id}"
            response = requests.get(
                api_url,
                headers=HEADERS,
            )
            comment_thread = ""
            if response.status_code == 200:
                comment_data = response.json()
                comment_thread += comment_data["content"]["raw"]
                if "parent" in comment_data:
                    # TODO - We should have a mechanism to stop this recursive call after let's say 7 times.
                    parent_comment_id = comment_data["parent"]["id"]
                    parent_thread = await BitbucketProcessor.fetch_comment_thread(payload, parent_comment_id, depth + 1)
                    comment_thread += "\n" + parent_thread
            return comment_thread
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing fetch_comment_thread : {e}")
            return ""
