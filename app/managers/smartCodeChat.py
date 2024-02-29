import asyncio

from sanic.log import logger

from app.managers.bitbucket.bitbucket_processor import BitbucketProcessor
from app.managers.openai_tools.openai_assistance import comment_processor


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict, comment) -> str:
        asyncio.ensure_future(cls.identify_annotation(payload, comment))
        return {"message": "Success"}

    @classmethod
    async def identify_annotation(cls, payload, comment: str):
        tag = "#AI_CODE_REVIEW"
        if comment.startswith(tag):
            remaining_text = comment[len(tag) :].strip()
            bb_payload = {"workspace": payload["repository"]["full_name"], "pr_id": payload["pullrequest"]["id"]}
            diff = await BitbucketProcessor.get_pr_diff(bb_payload)
            await cls.process_chat_comment(payload, remaining_text + diff)
        else:
            logger.info("The message does not start with the specified tag.")

    @classmethod
    async def process_chat_comment(cls, payload, context):
        comment_response = await comment_processor(context)
        # identify comment id
        # comment_id = ""
        # Line comment
        # comment_function = (
        #     BitbucketProcessor.create_comment_on_pr if payload.comment else BitbucketProcessor.create_comment_on_line
        # )
        # await comment_function(payload, comment_response)
        bb_payload = {"workspace": payload["repository"]["full_name"], "pr_id": payload["pullrequest"]["id"]}
        await BitbucketProcessor.create_comment_on_pr(bb_payload, comment_response)
