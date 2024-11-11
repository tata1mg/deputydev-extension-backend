from datetime import datetime, timezone
from typing import Dict, List

from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import (
    BucketStatus,
    BucketTypes,
    ExperimentStatusTypes,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.models.dao import PRComments
from app.main.blueprints.deputy_dev.models.dao.comment_bucket_mapping import (
    CommentBucketMapping,
)
from app.main.blueprints.deputy_dev.models.dto.bucket_dto import BucketDTO
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.bucket.bucket_service import BucketService
from app.main.blueprints.deputy_dev.services.code_review.helpers.pr_score_helper import (
    PRScoreHelper,
)
from app.main.blueprints.deputy_dev.services.comment.comment_bucket_mapping_Service import (
    CommentBucketMappingService,
)
from app.main.blueprints.deputy_dev.services.comment.pr_comments_service import (
    CommentService,
)
from app.main.blueprints.deputy_dev.services.db.db import DB
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService


class PRReviewPostProcessor:
    @classmethod
    async def post_process_pr_large_pr(cls, pr_dto: PullRequestDTO, tokens_data):
        await PRService.db_update(
            payload={"review_status": PrStatusTypes.REJECTED_LARGE_SIZE.value, "meta_info": {"tokens": tokens_data}},
            filters={"id": pr_dto.id},
        )
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={"review_status": ExperimentStatusTypes.REJECTED_LARGE_SIZE.value},
                filters={"repo_id": pr_dto.repo_id, "pr_id": pr_dto.id},
            )

    @classmethod
    async def post_process_pr_no_comments(cls, pr_dto: PullRequestDTO, tokens_data, extra_info: dict = None):
        await PRService.db_update(
            payload={
                "review_status": PrStatusTypes.COMPLETED.value,
                "meta_info": cls.pr_meta_info(pr_dto, tokens_data, extra_info=extra_info),
                "quality_score": cls.get_pr_score([], {}),
            },
            filters={"id": pr_dto.id},
        )
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={"review_status": ExperimentStatusTypes.COMPLETED.value, "llm_comment_count": 0},
                filters={"repo_id": pr_dto.repo_id, "pr_id": pr_dto.id},
            )

    @classmethod
    async def post_process_pr_experiment_purpose(cls, pr_dto: PullRequestDTO):
        await PRService.db_update(
            payload={
                "review_status": PrStatusTypes.REJECTED_EXPERIMENT.value,
            },
            filters={"id": pr_dto.id},
        )
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={"review_status": ExperimentStatusTypes.COMPLETED.value},
                filters={"repo_id": pr_dto.repo_id, "pr_id": pr_dto.id},
            )

    @classmethod
    async def post_process_pr(
        cls, pr_dto: PullRequestDTO, llm_comments: dict, tokens_data: dict, is_large_pr: bool, extra_info: dict = None
    ):
        if is_large_pr:
            await cls.post_process_pr_large_pr(pr_dto, tokens_data)
        elif llm_comments:
            await cls.post_process_pr_with_comments(pr_dto, llm_comments, tokens_data, extra_info)
        else:
            await cls.post_process_pr_no_comments(pr_dto, tokens_data, extra_info)

    @classmethod
    async def post_process_pr_with_comments(
        cls, pr_dto: PullRequestDTO, llm_comments, tokens_data, extra_info: dict = None
    ):
        buckets_data, comments = await cls.save_llm_comments(pr_dto, llm_comments)
        await cls.update_pr(pr_dto, comments, buckets_data, tokens_data, extra_info=extra_info)
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={
                    "review_status": ExperimentStatusTypes.COMPLETED.value,
                    "llm_comment_count": len(llm_comments),
                },
                filters={"repo_id": pr_dto.repo_id, "pr_id": pr_dto.id},
            )

    @classmethod
    def combine_all_agents_comments(cls, llm_agents_comments):
        all_comments = []

        for agent, data in llm_agents_comments.items():
            for comment in data.get("comments", []):
                if not comment.get("scm_comment_id"):
                    continue
                comment["agent"] = agent
                all_comments.append(comment)

        if not all_comments:
            raise ValueError("Failed to post comments on the VCS due to an error during the commenting process ")

        return all_comments

    @classmethod
    def get_pr_score(cls, llm_comments: list, buckets_data: Dict[str, BucketDTO]):
        weight_counts_data = {}
        for comment in llm_comments:
            for bucket in comment["buckets"]:
                if buckets_data[bucket].status == BucketStatus.ACTIVE.value:
                    weight_counts_data[buckets_data[bucket].weight] = (
                        weight_counts_data.get(buckets_data[bucket].weight, 0) + 1
                    )
        return PRScoreHelper.calculate_pr_score(weight_counts_data)

    @classmethod
    async def save_llm_comments(cls, pr_dto: PullRequestDTO, llm_comments: List[dict]):
        all_buckets = await BucketService.get_all_buckets_dict()
        new_buckets = []
        unique_buckets = set()
        for comment in llm_comments:
            for bucket in comment["buckets"]:
                if bucket not in all_buckets:
                    unique_buckets.add(bucket)

        for bucket in unique_buckets:
            new_buckets.append(
                BucketDTO(
                    **{
                        "name": bucket,
                        "weight": 0,
                        "bucket_type": BucketTypes.SUGGESTION.value,
                        "status": BucketStatus.INACTIVE.value,
                        "is_llm_suggested": True,
                    }
                )
            )

        if new_buckets:
            for bucket in new_buckets:
                await BucketService.db_insert(bucket)
            # reload buckets
            all_buckets = await BucketService.get_all_buckets_dict()

        comments_to_save = []
        bucket_mappings_to_save = []

        for comment in llm_comments:
            comment_info = {
                "iteration": 1,
                "llm_confidence_score": comment["confidence_score"],
                "llm_source_model": CONFIG.config["LLM_MODELS"][comment["model"]]["NAME"],
                "team_id": pr_dto.team_id,
                "scm": pr_dto.scm,
                "workspace_id": pr_dto.workspace_id,
                "repo_id": pr_dto.repo_id,
                "pr_id": pr_dto.id,
                "scm_comment_id": str(comment["scm_comment_id"]) if comment.get("scm_comment_id") is not None else None,
                "scm_author_id": pr_dto.scm_author_id,
                "author_name": pr_dto.author_name,
                "meta_info": {
                    "line_number": comment["line_number"],
                    "file_path": comment["file_path"],
                    "commit_id": pr_dto.commit_id,
                    "is_valid": comment["is_valid"],
                },
            }
            comments_to_save.append(PRComments(**comment_info))

        await CommentService.bulk_insert(comments_to_save)

        valid_llm_comments = [comment for comment in llm_comments if comment.get("scm_comment_id")]

        filters_to_fetch_inserted_comments = {
            "pr_id": pr_dto.id,
            "scm_comment_id__in": [str(c["scm_comment_id"]) for c in valid_llm_comments],
        }
        inserted_comments = await DB.get_by_filters(
            PRComments,
            filters=filters_to_fetch_inserted_comments,
        )

        for comment, pr_comment in zip(valid_llm_comments, inserted_comments):
            for bucket in comment["buckets"]:
                bucket_id = all_buckets[bucket].id
                bucket_mappings_to_save.append(CommentBucketMapping(pr_comment_id=pr_comment.id, bucket_id=bucket_id))
        await CommentBucketMappingService.bulk_insert(bucket_mappings_to_save)

        return all_buckets, llm_comments

    @classmethod
    async def update_pr(cls, pr_dto: PullRequestDTO, llm_comments, buckets_data, tokens_data, extra_info: dict = None):
        pr_score = cls.get_pr_score(llm_comments, buckets_data)
        await PRService.db_update(
            payload={
                "review_status": PrStatusTypes.COMPLETED.value,
                "meta_info": cls.pr_meta_info(pr_dto, tokens_data, llm_comments=llm_comments, extra_info=extra_info),
                "quality_score": pr_score,
            },
            filters={"id": pr_dto.id},
        )

    @classmethod
    def pr_meta_info(cls, pr_dto: PullRequestDTO, tokens_data, llm_comments: dict = None, extra_info: dict = None):
        llm_comments, extra_info = llm_comments or [], extra_info or {}
        return {
            "pr_review_tat_in_secs": int(
                (datetime.now(timezone.utc) - pr_dto.scm_creation_time.astimezone(timezone.utc)).total_seconds()
            ),
            "execution_time_in_secs": int((datetime.now() - extra_info["execution_start_time"]).total_seconds()),
            "tokens": cls.format_token(tokens_data)["tokens"],
            "total_comments": len(llm_comments),
            "issue_id": extra_info.get("issue_id"),
            "confluence_id": extra_info.get("confluence_doc_id"),
        }

    @classmethod
    def format_token(cls, tokens_data: dict):
        tokens = {}
        for agent_name, agent_tokens in tokens_data.items():
            tokens[agent_name] = agent_tokens
        return {"tokens": tokens}
