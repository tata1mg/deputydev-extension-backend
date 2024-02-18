import json
from datetime import datetime

import requests
from torpedo import CONFIG

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
        print(payload)
        print("payload", payload)
        diff_url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}"
        print("diff_url", diff_url)
        response = requests.get(
            diff_url,
            headers=HEADERS,
        ).json()
        print(response)

        created_time = datetime.fromisoformat(response["created_on"][:-6])
        updated_time = datetime.fromisoformat(response["updated_on"][:-6])

        # Calculate the time difference in minutes
        time_difference = (updated_time - created_time).total_seconds() / 60

        # Print the time difference in minutes
        print(f"Time difference: {time_difference} minutes")
        if time_difference > 5:
            return True
        else:
            return False

    @staticmethod
    async def create_comment_on_line(payload, comment: dict):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        comment_payload = {
            # TODO - Indcude tripple quotes only if there is any code. Add it behind an if check.
            "content": {"raw": comment.get("comment") + "\n ```" + comment.get("corrective_code") + "```"},
            "inline": {
                "path": comment.get("file_path"),
                "to": comment.get("line_number"),
            },
        }
        response = requests.post(url, headers=HEADERS, json=comment_payload)
        return response.json()

    @staticmethod
    async def create_comment_on_pr(payload):
        url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/comments"
        payload = json.dumps(
            {"content": {"raw": "size is PR is too long, kindly create a pr with less then 3500 char."}}
        )
        response = requests.post(url, headers=HEADERS, json=payload)
        return response.json()

    @staticmethod
    async def get_pr_diff(payload):
        diff_url = f"{URL}/{payload.get('workspace')}/pullrequests/{payload.get('pr_id')}/diff"
        response = requests.get(
            diff_url,
            headers=HEADERS,
        )
        return response.text
