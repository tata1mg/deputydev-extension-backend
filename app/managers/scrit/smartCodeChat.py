import asyncio

from sanic.log import logger

from app.managers.openai_tools.openai_assistance import comment_processor
from app.service_clients.bitbucket.bitbucket_processor import BitbucketProcessor
from app.utils import get_comment


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict):
        comment_payload = get_comment(payload)
        logger.info(f"Comment payload: {comment_payload}")
        asyncio.ensure_future(cls.identify_annotation(payload, comment_payload))
        return

    @classmethod
    async def identify_annotation(cls, payload, comment_payload):
        tag = "#scrit"
        comment = comment_payload.get("comment").lower()
        if tag in comment:
            logger.info(f"Processing the comment: {comment} , with payload : {payload}")
            bb_payload = {"workspace": payload["repository"]["full_name"], "pr_id": payload["pullrequest"]["id"]}
            diff = await BitbucketProcessor.get_pr_diff(bb_payload)
            await cls.process_chat_comment(payload, comment + diff, comment_payload)

    @classmethod
    async def process_chat_comment(cls, payload, context, comment_payload):
        logger.info("process_chat_comment")
        bb_payload = {"workspace": payload["repository"]["full_name"], "pr_id": payload["pullrequest"]["id"]}
        get_comment_thread = await BitbucketProcessor.fetch_comment_thread(bb_payload, payload["comment"]["id"])
        get_comment_thread = f"Comment Thread : {get_comment_thread} , questions and PR diff: {context}"
        comment_response = await comment_processor(get_comment_thread + context)
        logger.info(f"Process chat comment response: {comment_response}")
        # This validation will determine the origin of the request,
        # such as whether it's a reply to an existing comment or a PR-level comment.
        if "parent" in comment_payload:
            await BitbucketProcessor.create_comment_on_comment(bb_payload, comment_response, comment_payload)
        else:
            await BitbucketProcessor.create_comment_on_pr(bb_payload, comment_response)
