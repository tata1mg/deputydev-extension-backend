import asyncio
from typing import Union

from sanic.log import logger

from app.constants.constants import CONFIDENCE_SCORE
from app.managers.bitbucket.bitbucket_processor import BitbucketProcessor
from app.managers.openai_tools.openai_assistance import (
    create_review_thread,
    create_run_id,
    poll_for_success,
)


class SmartCodeManager:
    @classmethod
    async def process_pr_review(cls, data) -> dict[str, Union[str, int]]:
        asyncio.ensure_future(cls.background_task(data))
        # TODO - What is the point of returning this dict? Why can't we return just a string message from here?
        return {"status": "Success", "message": "Processing started."}

    @staticmethod
    async def background_task(data):
        payload = {
            "workspace": data.get("repo_name").strip(),
            "pr_id": data.get("pr_id").strip(),
            "confidence_score": data.get("confidence_score", CONFIDENCE_SCORE),
        }
        is_update_pr = await BitbucketProcessor.get_pr_details(payload)
        if "pr_type" not in data:
            logger.error("pr_type is not present in your request.")
            # TODO - What is the point of returning this dict? Why can't we return just a string message from here?
            return {
                "status": "Bad Request",
                "message": "pr_type is not present in your request.",
            }
        if data["pr_type"] == "created":
            if is_update_pr:
                return
        else:
            logger.info("Processing started.")
            diff = await BitbucketProcessor.get_pr_diff(payload)
            if (diff.count("\n+") + diff.count("\n-")) > 10000:
                # TODO - We decided to smartly calculate the diff based on +/- numbers we get against each file in diff
                logger.info("Diff count is {}. unable to process this request.".format(len(diff)))
                comment = "size is PR is too long, kindly create a pr with less then 3500 char"
                await BitbucketProcessor.create_comment_on_pr(payload, comment)
            # TODO - we should also add PR description in context we are providing to LLM.
            thread = await create_review_thread(diff)
            run = await create_run_id(thread)
            response = await poll_for_success(thread, run)
            if response:
                for comment in response.get("comments"):
                    if comment.get("confidence_score") > float(payload.get("confidence_score")):
                        await BitbucketProcessor.create_comment_on_line(payload, comment)
            # TODO - I remember we decided to return requestId back to user. So that they can come back to us with
            #  that requestId and we should be able to find out what happened in our logs pivoting over that requestId.
            return

    @staticmethod
    async def background_logical_task():
        logger.info("Logical processing started.")
        return

    @classmethod
    async def chat(cls, data):
        return
