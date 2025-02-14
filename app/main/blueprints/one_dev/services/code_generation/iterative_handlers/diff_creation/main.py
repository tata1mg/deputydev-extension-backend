from typing import Any, Dict, List, Tuple

from prompts.dataclasses.main import PromptFeatures
from prompts.factory import PromptFeatureFactory

from app.backend_common.services.llm.dataclasses.main import LLMMeta, LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.services.repo.repo_factory import RepoFactory
from app.common.utils.app_logger import AppLogger
from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO
from app.main.blueprints.one_dev.services.code_generation.helpers.code_application import (
    CodeApplicationHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.base_code_gen_iterative_handler import (
    BaseCodeGenIterativeHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.dataclass.main import (
    CodeGenIterativeHandlers,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.diff_creation.dataclasses.main import (
    DiffCreationInput,
)
from app.main.blueprints.one_dev.services.code_generation.utils.utils import (
    get_chunks_by_file_total_lines,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)


class DiffCreationHandler(BaseCodeGenIterativeHandler[DiffCreationInput]):
    feature = CodeGenIterativeHandlers.DIFF_CREATION

    @classmethod
    async def _create_pr_with_generated_diff(
        cls, payload: DiffCreationInput, diff: Dict[str, List[Tuple[int, int, str]]], commit_message: str, pr_title: str
    ) -> Dict[str, Any]:
        if not payload.pr_config:
            raise ValueError("PR Config is required to apply the diff")
        registered_repo = await RepoFactory.get_repo_by_workspace_id_and_name(
            payload.pr_config.workspace_id, payload.pr_config.repo_name
        )
        _local_repo, is_cloned = await registered_repo.clone_branch(
            branch_name=payload.pr_config.parent_source_branch,
            repo_dir_prefix=payload.session_id,
        )

        if not is_cloned:
            raise ValueError("Failed to clone the repo")

        code_application_handler = CodeApplicationHandler(
            repo_path=registered_repo.repo_dir,
            repo_service=registered_repo,
            diff=diff,
            commit_message=commit_message,
            pr_title=pr_title,
        )

        existing_pr, pr_link = await code_application_handler.create_or_update_pr(
            destination_branch=payload.pr_config.destination_branch,
            source_branch=payload.pr_config.source_branch,
            pr_title_prefix=payload.pr_config.pr_title_prefix,
            commit_message_prefix=payload.pr_config.commit_message_prefix,
        )

        # delete the cloned repo
        registered_repo.delete_local_repo()

        return {
            "pr_link": pr_link,
            "existing_pr": existing_pr,
        }

    @classmethod
    async def _feature_task(cls, payload: DiffCreationInput, job_id: int, llm_meta: List[LLMMeta]) -> Dict[str, Any]:

        previous_responses = await cls._get_previous_responses(payload)
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.DIFF_CREATION,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={},
        )
        llm_response = await LLMHandler(prompt_handler=prompt).get_llm_response_data(
            previous_responses=previous_responses
        )
        llm_meta.append(llm_response.llm_meta)
        code_lines = get_chunks_by_file_total_lines(llm_response.parsed_llm_data["chunks_by_file"])
        await JobService.db_update(
            filters={"id": job_id},
            update_data={
                "status": "LLM_RESPONSE",
                "meta_info": {
                    "llm_meta": [meta.model_dump(mode="json") for meta in llm_meta],
                },
            },
        )
        await SessionChatService.db_create(
            SessionChatDTO(
                session_id=payload.session_id,
                prompt_type=PromptFeatures.DIFF_CREATION,
                llm_prompt=llm_response.raw_prompt,
                llm_response=llm_response.raw_llm_response,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET.value,
                response_summary="",
                user_query="generate diff",
                code_lines_count=code_lines,
            )
        )

        if not llm_response.parsed_llm_data["chunks_by_file"]:
            raise ValueError("Failed to generate diff")

        final_resp: Dict[str, Any] = {
            "session_id": payload.session_id,
            "diff": llm_response.parsed_llm_data["chunks_by_file"],
            "pr_title": llm_response.parsed_llm_data["pr_title"],
            "commit_message": llm_response.parsed_llm_data["commit_message"],
        }

        if not (payload.pr_config):
            return final_resp

        try:
            application_resp = await cls._create_pr_with_generated_diff(
                payload=payload,
                diff=final_resp["diff"],
                commit_message=final_resp["commit_message"],
                pr_title=final_resp["pr_title"],
            )
            await JobService.db_update(
                filters={"id": job_id},
                update_data={"status": "DIFF_APPLIED"},
            )
            final_resp.update(application_resp)
        except Exception as ex:
            AppLogger.log_error(f"PR creation failed - {str(ex)}")
        return final_resp

    @classmethod
    async def generate_diff_for_current_job(
        cls, payload: DiffCreationInput, job_id: int, llm_meta: List[LLMMeta]
    ) -> Dict[str, Any]:
        return await cls._feature_task(payload=payload, job_id=job_id, llm_meta=llm_meta)
