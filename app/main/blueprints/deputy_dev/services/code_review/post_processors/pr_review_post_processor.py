from datetime import datetime, timezone
from typing import List

from torpedo import CONFIG

from app.backend_common.repository.db import DB
from app.backend_common.services.pr.base_pr import BasePR
from app.common.utils.app_logger import AppLogger
from app.common.utils.context_vars import get_context_value
from app.main.blueprints.deputy_dev.constants.constants import (
    CODE_REVIEW_ERRORS,
    ExperimentStatusTypes,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.models.dao.postgres import (
    AgentCommentMappings,
    Agents,
    PRComments,
)
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.code_review.helpers.pr_score_helper import (
    PRScoreHelper,
)
from app.main.blueprints.deputy_dev.services.comment.affirmation_comment_service import (
    AffirmationService,
)
from app.main.blueprints.deputy_dev.services.comment.agent_comment_mapping_Service import (
    AgentCommentMappingService,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.pr_comments_service import (
    CommentService,
)
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)

config = CONFIG.config


class PRReviewPostProcessor:
    def __init__(self, pr_service: BasePR, comment_service: BaseComment, affirmation_service: AffirmationService):
        self.pr_service = pr_service
        self.comment_service = comment_service
        self.pr_model = pr_service.pr_model()
        self.affirmation_service = affirmation_service
        self.completed_pr_count = 0
        self.review_status = None
        self.loc_changed = 0

    async def post_process_pr_large_pr(self, pr_dto: PullRequestDTO, tokens_data):
        self.review_status = PrStatusTypes.REJECTED_LARGE_SIZE.value
        await PRService.db_update(
            payload={
                "review_status": self.review_status,
                "meta_info": {"tokens": tokens_data},
                "iteration": self.completed_pr_count + 1,
                "loc_changed": self.loc_changed,
            },
            filters={"id": pr_dto.id},
        )
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={"review_status": ExperimentStatusTypes.REJECTED_LARGE_SIZE.value},
                filters={"repo_id": pr_dto.repo_id, "pr_id": pr_dto.id},
            )

    async def post_process_pr_no_comments(self, pr_dto: PullRequestDTO, tokens_data, extra_info: dict = None):
        self.review_status = PrStatusTypes.COMPLETED.value
        await PRService.db_update(
            payload={
                "review_status": self.review_status,
                "meta_info": self.pr_meta_info(pr_dto, tokens_data, extra_info=extra_info),
                "quality_score": self.get_pr_score([]),
                "iteration": self.completed_pr_count + 1,
                "loc_changed": self.loc_changed,
            },
            filters={"id": pr_dto.id},
        )
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={"review_status": ExperimentStatusTypes.COMPLETED.value, "llm_comment_count": 0},
                filters={"repo_id": pr_dto.repo_id, "pr_id": pr_dto.id},
            )

    @staticmethod
    async def post_process_pr_experiment_purpose(pr_dto: PullRequestDTO):
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

    async def post_process_pr(
        self,
        pr_dto: PullRequestDTO,
        llm_comments: List[dict],
        tokens_data: dict,
        is_large_pr: bool,
        extra_info: dict = None,
    ):
        self.loc_changed = await self.pr_service.get_loc_changed_count()
        self.completed_pr_count = await PRService.get_completed_pr_count(pr_dto)

        print(1)
        if is_large_pr:
            await self.post_process_pr_large_pr(pr_dto, tokens_data)
        elif llm_comments:
            AppLogger.log_warn(f"Comments on PR: {llm_comments}")
            await self.post_process_pr_with_comments(pr_dto, llm_comments, tokens_data, extra_info)
        else:
            await self.post_process_pr_no_comments(pr_dto, tokens_data, extra_info)
        await self.process_affirmation_message()

    async def process_affirmation_message(self):
        error_message = SettingService.fetch_setting_errors(CODE_REVIEW_ERRORS)
        additional_context = {"error": f"\n\n{error_message}" if error_message else ""}
        await self.affirmation_service.create_affirmation_reply(
            message_type=self.review_status, commit_id=self.pr_model.commit_id(), additional_context=additional_context
        )

    async def post_process_pr_with_comments(
        self, pr_dto: PullRequestDTO, llm_comments, tokens_data, extra_info: dict = None
    ):
        comments = await self.save_llm_comments(pr_dto, llm_comments)
        await self.update_pr(pr_dto, comments, tokens_data, extra_info=extra_info)
        if ExperimentService.is_eligible_for_experiment():
            await ExperimentService.db_update(
                payload={
                    "review_status": ExperimentStatusTypes.COMPLETED.value,
                    "llm_comment_count": len(llm_comments),
                },
                filters={"repo_id": pr_dto.repo_id, "pr_id": pr_dto.id},
            )

    @staticmethod
    def combine_all_agents_comments(llm_agents_comments):
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

    @staticmethod
    def get_pr_score(llm_comments: list):
        weight_counts_data = {}
        agent_settings = get_context_value("setting")["code_review_agent"]["agents"]
        agents_by_agent_id = {agent_data["agent_id"]: agent_data for agent_name, agent_data in agent_settings.items()}
        for comment in llm_comments:
            for bucket in comment["buckets"]:
                weight = agents_by_agent_id[bucket["agent_id"]]["weight"]
                weight_counts_data[weight] = weight_counts_data.get(weight, 0) + 1
        return PRScoreHelper.calculate_pr_score(weight_counts_data)

    @staticmethod
    async def save_llm_comments(pr_dto: PullRequestDTO, llm_comments: List[dict]):
        comments_to_save = []
        agent_mappings_to_save = []

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
        agent_ids = []
        for comment in valid_llm_comments:
            for bucket in comment.get("buckets") or []:
                agent_ids.append(bucket["agent_id"])
        agent_filter = {"repo_id": pr_dto.repo_id, "agent_id__in": agent_ids}
        agents = await DB.get_by_filters(
            Agents,
            filters=agent_filter,
        )
        agents_by_id = {str(agent.agent_id): agent for agent in agents}
        comments_by_ids = {}
        inserted_comments_dict = {comment.scm_comment_id: comment for comment in inserted_comments}
        for valid_comment in valid_llm_comments:
            scm_comment_id = str(valid_comment["scm_comment_id"])
            if scm_comment_id in inserted_comments_dict:
                inserted_comment = inserted_comments_dict[scm_comment_id]
                comments_by_ids[inserted_comment.id] = valid_comment
        agent_settings = get_context_value("setting")["code_review_agent"]["agents"]
        agents_by_agent_id = {agent_data["agent_id"]: agent_data for agent_name, agent_data in agent_settings.items()}
        for comment_id, comment_data in comments_by_ids.items():
            # fetch all agents based on "agent_id" and "repo_id"
            # save in agent_comment_mapping table
            for bucket in comment_data["buckets"]:
                agent_id = bucket["agent_id"]
                if agent_id in agents_by_id:
                    agent = agents_by_id[agent_id]
                    agent_mappings_to_save.append(
                        AgentCommentMappings(
                            pr_comment_id=comment_id, agent_id=agent.id, weight=agents_by_agent_id[agent_id]["weight"]
                        )
                    )
        await AgentCommentMappingService.bulk_insert(agent_mappings_to_save)
        return llm_comments

    async def update_pr(self, pr_dto: PullRequestDTO, llm_comments, tokens_data, extra_info: dict = None):
        pr_score = self.get_pr_score(llm_comments)
        self.review_status = PrStatusTypes.COMPLETED.value
        await PRService.db_update(
            payload={
                "review_status": self.review_status,
                "meta_info": self.pr_meta_info(pr_dto, tokens_data, llm_comments=llm_comments, extra_info=extra_info),
                "quality_score": pr_score,
                "iteration": self.completed_pr_count + 1,
                "loc_changed": self.loc_changed,
            },
            filters={"id": pr_dto.id},
        )

    def pr_meta_info(self, pr_dto: PullRequestDTO, tokens_data, llm_comments: dict = None, extra_info: dict = None):
        llm_comments, extra_info = llm_comments or [], extra_info or {}
        return {
            "pr_review_tat_in_secs": int(
                (datetime.now(timezone.utc) - pr_dto.scm_creation_time.astimezone(timezone.utc)).total_seconds()
            ),
            "execution_time_in_secs": int((datetime.now() - extra_info["execution_start_time"]).total_seconds()),
            "tokens": self.format_token(tokens_data)["tokens"],
            "total_comments": len(llm_comments),
            "issue_id": extra_info.get("issue_id"),
            "confluence_id": extra_info.get("confluence_doc_id"),
        }

    @staticmethod
    def format_token(tokens_data: dict):
        tokens = {}
        for agent_name, agent_tokens in tokens_data.items():
            tokens[agent_name] = agent_tokens
        return {"tokens": tokens}
