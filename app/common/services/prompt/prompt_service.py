from app.main.blueprints.deputy_dev.constants.prompts.v1.system_prompts import (
    SCRIT_PROMPT,
)
from app.main.blueprints.deputy_dev.constants.prompts.v2.system_prompts import (
    SCRIT_PROMPT as SCRIT_PROMPT_v2,
)
from app.main.blueprints.deputy_dev.services.bucket.bucket_service import BucketService


class PromptService:
    @classmethod
    async def build_pr_review_prompt(cls, prompt_version):
        if prompt_version == "v1":
            prompt = await cls.__build_prompt_version_v1()
            return prompt
        elif prompt_version == "v2":
            prompt = await cls.__build_prompt_version_v2()
            return prompt

    @classmethod
    async def __build_prompt_version_v1(cls):
        return SCRIT_PROMPT

    @classmethod
    async def __build_prompt_version_v2(cls):
        all_buckets = await BucketService.get_published_buckets()
        if not all_buckets:
            raise ValueError("buckets data not found")
        bucket_prompt = cls.__build_bucket_prompt(all_buckets)
        final_prompt = SCRIT_PROMPT_v2 + bucket_prompt
        return final_prompt

    @classmethod
    def __build_bucket_prompt(cls, buckets: dict):
        bucket_prompt = ""
        single_bucket_prompt = """
        {row_number}. {bucket_name} \n
                {bucket_description}
            """
        for index, bucket in enumerate(buckets):
            bucket_prompt += "\n" + single_bucket_prompt.format(
                row_number=index + 1, bucket_name=bucket["name"], bucket_description=bucket["description"]
            )
        return bucket_prompt
