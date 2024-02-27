import asyncio

from sanic.log import logger

from app.managers.bitbucket.bitbucket_processor import BitbucketProcessor
from app.managers.openai_tools.openai_assistance import comment_processor


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict) -> str:
        asyncio.ensure_future(cls.identify_annotation(payload))
        return {"message": "Success"}

    @classmethod
    async def identify_annotation(cls, payload: dict):
        comment = payload.get("comment")
        tag = "#AI_CODE_REVIEW"
        if comment.startswith(tag):
            remaining_text = comment[len(tag) :].strip()
            await cls.process_comment(payload, remaining_text)
        else:
            logger.info("The message does not start with the specified tag.")

    @classmethod
    async def process_comment(cls, payload, comment):
        comment_response = await comment_processor(comment)
        # identify comment id
        # comment_id = ""
        # Line comment
        comment_function = (
            BitbucketProcessor.create_comment_on_pr if payload.comment else BitbucketProcessor.create_comment_on_line
        )
        await comment_function(payload, comment_response)
