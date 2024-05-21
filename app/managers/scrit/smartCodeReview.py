import asyncio

from sanic.log import logger

from app.constants.constants import PR_SIZE_TOO_BIG_MESSAGE
from app.managers.openai_tools.openai_assistance import (
    create_review_thread,
    create_run_id,
    poll_for_success,
)
from app.service_clients.bitbucket.bitbucket_processor import BitbucketProcessor
from app.utils import calculate_total_diff


class SmartCodeManager:
    @classmethod
    async def process_pr_review(cls, data):
        asyncio.ensure_future(cls.background_task(data))
        return

    @staticmethod
    async def background_task(data):
        payload = {
            "workspace": data.get("repo_name").strip(),
            "pr_id": data.get("pr_id").strip(),
            "confidence_score": data.get("confidence_score"),
        }
        pr_detail = await BitbucketProcessor.get_pr_details(payload)
        if data["pr_type"] == "created" and not pr_detail["created"]:
            return
        else:
            logger.info("Processing started.")
            diff = await BitbucketProcessor.get_pr_diff(payload)
            diff_loc = calculate_total_diff(diff)
            logger.info(f"Total diff LOC is {diff_loc}")
            if diff_loc > 350:
                logger.info("Diff count is {}. unable to process this request.".format(diff_loc))
                comment = PR_SIZE_TOO_BIG_MESSAGE.format(diff_loc)
                await BitbucketProcessor.create_comment_on_pr(payload, comment)
                return
            thread = await create_review_thread(diff, pr_detail)
            run = await create_run_id(thread)
            response = await poll_for_success(thread, run)
            if response:
                comments = response.get("comments")
                logger.info("PR comments: {}".format(comments))
                if any(
                    float(comment.get("confidence_score")) >= float(payload.get("confidence_score"))
                    for comment in comments
                ):
                    for comment in comments:
                        if float(comment.get("confidence_score")) >= float(payload.get("confidence_score")):
                            await BitbucketProcessor.create_comment_on_line(payload, comment)
                else:
                    logger.info("LGTM!")
                    await BitbucketProcessor.create_comment_on_pr(payload, "LGTM!")
            return
