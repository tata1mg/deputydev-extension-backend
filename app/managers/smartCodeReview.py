import asyncio
from typing import Union

from app.managers.bitbucket.bitbucket_processor import BitbucketProcessor
from app.managers.openai_tools.openai_assistance import (
    create_review_thread,
    create_run_id,
    poll_for_success,
)


class SmartCodeManager:
    @classmethod
    async def process_pr_review(cls, data) -> dict[str, Union[str, int]]:
        payload = {
            "workspace": data.get("repo_name").strip(),
            "pr_id": data.get("pr_id").strip(),
        }
        is_update_pr = await BitbucketProcessor.get_pr_details(payload)
        if "pr_type" not in data:
            print("pr_type is not present in your request.")
            return {
                "status": "Bad Request",
                "message": "pr_type is not present in your request.",
            }
        if data["pr_type"] == "created":
            if is_update_pr:
                print("This is a updated PR.")
                return {"status": "Bad Request", "message": "This is a updated PR."}
        else:
            asyncio.ensure_future(cls.background_task(payload))
            return {"status": "Success", "message": "Processing started."}

    @staticmethod
    async def background_task(payload):
        print("Processing started.")
        diff = await BitbucketProcessor.get_pr_diff(payload)
        thread = await create_review_thread(diff)
        run = await create_run_id(thread)
        response = await poll_for_success(thread, run)
        if response:
            print(response)
            for i in response:
                await BitbucketProcessor.create_comment_on_line(payload, i)

        return
