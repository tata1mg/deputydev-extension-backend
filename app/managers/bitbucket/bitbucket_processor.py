import logging
from datetime import datetime

import requests
from torpedo import CONFIG
import re

from app.constants.constants import IGNORE_FILES

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
            return True
        else:
            return False

    @staticmethod
    async def create_comment_on_line(payload, comment: dict):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        comment_payload = {
            "content": {"raw": comment.get("comment")},
            "inline": {
                "path": comment.get("file_path")[2:]
                if re.match(r"^[ab]", comment.get("file_path"))
                else comment.get("file_path"),
                "to": comment.get("line_number"),
            },
        }
        # Check if there is corrective code before adding it to the payload
        if comment.get("corrective_code") and len(comment.get("corrective_code")) > 0:
            comment_payload["content"]["raw"] += f" \n ```{comment.get('corrective_code')}```"
        response = requests.post(url, headers=HEADERS, json=comment_payload)
        return response.json()

    @staticmethod
    async def create_comment_on_comment(payload, comment, comment_payload):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        # TODO - Will this be able to add code blocks as part of comments?
        comment_payload = {
            "content": {"raw": comment},
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
        resp_text = ""
        for d in response.text.split("diff --git "):
            if not any(keyword in d for keyword in IGNORE_FILES):
                resp_text += d
        return resp_text

    @staticmethod
    async def fetch_comment_thread(payload, comment_id):
        try:
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
                    parent_comment_id = comment_data["parent"]["id"]
                    # TODO - We should have a mechanism to stop this recursive call after let's say 7 times.
                    parent_thread = await BitbucketProcessor.fetch_comment_thread(payload, parent_comment_id)
                    comment_thread += "\n" + parent_thread
            return comment_thread
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing fetch_comment_thread : {e}")
            return ""
