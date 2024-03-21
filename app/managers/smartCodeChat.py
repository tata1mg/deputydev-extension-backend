import asyncio

from sanic.log import logger

from app.managers.bitbucket.bitbucket_processor import BitbucketProcessor
from app.managers.openai_tools.openai_assistance import comment_processor

# TODO - Create a new package called `scrit` - Put all manager files inside it.


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict, comment) -> str:
        asyncio.ensure_future(cls.identify_annotation(payload, comment))
        # TODO - I don't think we should return dict.
        return {"message": "Success"}

    @classmethod
    async def identify_annotation(cls, payload, comment_payload: str):
        tag = "#SCRIT"
        comment = comment_payload["comment"]
        if comment.startswith(tag):
            # TODO - `#SCRIT` should be present in the comment. Not necessarily only at the starting of the comment.
            remaining_text = comment[len(tag) :].strip()
            bb_payload = {"workspace": payload["repository"]["full_name"], "pr_id": payload["pullrequest"]["id"]}
            diff = await BitbucketProcessor.get_pr_diff(bb_payload)
            await cls.process_chat_comment(payload, remaining_text + diff, comment_payload)
        else:
            # TODO - No need to log this.
            logger.info("The message does not start with the specified tag.")

    @classmethod
    async def process_chat_comment(cls, payload, context, comment_payload):
        # TODO - Whenever logging such stuff, we should always log it with requestId.
        #  How are we going to create a trail of request looking at logs?
        logger.info(f"context : {context}")
        bb_payload = {"workspace": payload["repository"]["full_name"], "pr_id": payload["pullrequest"]["id"]}
        get_comment_thread = await BitbucketProcessor.fetch_comment_thread(bb_payload, payload["comment"]["id"])
        get_comment_thread = f"Comment Thread : {get_comment_thread} , questions and PR diff: {context}"
        comment_response = await comment_processor(get_comment_thread + context)
        # TODO - What is this if check about?
        if "parent" in comment_payload:
            await BitbucketProcessor.create_comment_on_comment(bb_payload, comment_response, comment_payload)
        else:
            await BitbucketProcessor.create_comment_on_pr(bb_payload, comment_response)
