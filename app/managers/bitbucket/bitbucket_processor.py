import json
from datetime import datetime

import requests
from torpedo import CONFIG

from app.constants.constants import IGNORE_FILES

config = CONFIG.config

URL = config.get("BITBUCKET_URL")
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": config.get("BITBUCKET_KEY"),
}


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
        print(response)

        if not response:
            raise ValueError("Invalid PR.")

        created_time = datetime.fromisoformat(response["created_on"][:-6])
        updated_time = datetime.fromisoformat(response["updated_on"][:-6])

        # Calculate the time difference in minutes
        time_difference = (updated_time - created_time).total_seconds() / 60

        # Print the time difference in minutes
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
                "path": comment.get("file_path"),
                "to": comment.get("line_number"),
            },
        }
        # Check if there is corrective code before adding it to the payload
        if comment.get("corrective_code"):
            comment_payload["content"]["raw"] += f"\n ```{comment.get('corrective_code')}```"
        response = requests.post(url, headers=HEADERS, json=comment_payload)
        return response.json()

    @staticmethod
    async def create_comment_on_pr(payload, comment):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        payload = json.dumps(
            {"content": {"raw": "size is PR is too long, kindly create a pr with less then 3500 char."}}
        )
        comment_payload = {"content": {"raw": comment.get("comment")}}
        comment_payload["content"]["raw"] += f"\n ```{comment.get('corrective_code')}```"

        response = requests.post(url, headers=HEADERS, json=payload)
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
            print(d)
            if not any(keyword in d for keyword in IGNORE_FILES):
                resp_text += d
        return resp_text
