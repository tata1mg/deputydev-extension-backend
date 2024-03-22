import asyncio
from typing import Union

from sanic.log import logger

from app.constants.constants import CONFIDENCE_SCORE
from app.managers.openai_tools.openai_assistance import (
    create_review_thread,
    create_run_id,
    poll_for_success,
)
from app.service_clients.bitbucket.bitbucket_processor import BitbucketProcessor
from app.utils import calculate_total_diff


class SmartCodeManager:
    @classmethod
    async def process_pr_review(cls, data) -> dict[str, Union[str, int]]:
        asyncio.ensure_future(cls.background_task(data))
        # TODO - What is the point of returning this dict? Why can't we return just a string message from here?
        return

    @staticmethod
    async def background_task(data):
        payload = {
            "workspace": data.get("repo_name").strip(),
            "pr_id": data.get("pr_id").strip(),
            "confidence_score": data.get("confidence_score", CONFIDENCE_SCORE),
        }
        pr_detail = await BitbucketProcessor.get_pr_details(payload)
        if data["pr_type"] == "created" and not pr_detail["created"]:
            # TODO - What is the point of returning this dict? Why can't we return just a string message from here?
            return
        else:
            logger.info("Processing started.")
            diff = await BitbucketProcessor.get_pr_diff(payload)
            # TODO - We decided to smartly calculate the diff based on +/- numbers we get against each file in diff
            if calculate_total_diff(diff) > 350:
                logger.info("Diff count is {}. unable to process this request.".format(len(diff)))
                comment = "The size of the PR is excessive. Please create a PR with fewer than 350 lines."
                await BitbucketProcessor.create_comment_on_pr(payload, comment)
            # TODO - we should also add PR description in context we are providing to LLM.
            thread = await create_review_thread(diff, pr_detail)
            run = await create_run_id(thread)
            response = await poll_for_success(thread, run)
            if response:
                comments = response.get("comments")
                # TODO - If there are no comments from LLM, just add a global comment saying `LGTM :)`
                logger.info("PR comments: {}".format(comments))
                if len(comments) > 0:
                    for comment in response.get("comments"):
                        if float(comment.get("confidence_score")) > float(payload.get("confidence_score")):
                            await BitbucketProcessor.create_comment_on_line(payload, comment)
                else:
                    logger.info("LGTM!")
                    await BitbucketProcessor.create_comment_on_pr(
                        payload, "LGTM! Code looks clean and well-structured. Nice work!"
                    )
                # TODO - I remember we decided to return requestId back to user. So that they can come back to us with
                #  that requestId and we should be able to find out
                #  what happened in our logs pivoting over that requestId.

            return
