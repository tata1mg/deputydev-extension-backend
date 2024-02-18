import asyncio
from typing import Union

from sanic.log import logger

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
            # TODO - Remove all print statements and replace them with loggers where it makes sense.
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
        if (diff.count("\n+") + diff.count("\n-")) > 10000:
            logger.info("Diff count is {}. unable to process this request.".format(len(diff)))
            await BitbucketProcessor.create_comment_on_pr(payload)
        thread = await create_review_thread(diff)
        run = await create_run_id(thread)
        response = await poll_for_success(thread, run)
        if response:
            for comment in response.get('comments'):
                # TODO Get this confidence score threshold as a query param from customers.
                if comment.get('confidence_score') > 0.72:
                    await BitbucketProcessor.create_comment_on_line(payload, comment)

        return
