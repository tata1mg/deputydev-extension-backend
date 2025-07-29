from sanic.log import logger

from app.backend_common.services.pr.pr_factory import PRFactory
from app.backend_common.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.constants.constants import Feature
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.code_generation.code_generation_handler import (
    CodeGenerationHandler,
)
from app.main.blueprints.deputy_dev.utils import get_vcs_auth_handler


class SuggestionCodeGenerationManager:
    DESTINATION_BRANCH_PATTERN = r"destination_branch:\s*([^\s\n]+)"  # branch:<branch_name> pattern
    SOURCE_BRANCH_PATTERN = r"source_branch:\s*([^\s\n]+)"  # branch:<branch_name> pattern
    QUERY_PATTERN = r"query:\s*([^\n]*(?:\n(?!branch:)[^\n]*)*)"
    CREATE_PR_COMMAND = "#create_pr"
    SUGGESTION_COMMAND = "#suggestion"
    PR_URL_PATTERN = r"(https?://[^\s]+)"

    @classmethod
    async def process_suggestion(cls, comment_payload: ChatRequest, vcs_type: str):
        """Handle suggestion command"""
        # Get PR details for branch information
        repo_service = await cls.initialize_repo(comment_payload, vcs_type)

        _, is_repo_cloned = await repo_service.clone_branch()

        if not is_repo_cloned:
            logger.error("Failed to clone repository")
            return
        try:
            pr_model = repo_service.pr_model()
            pr_diff = await repo_service.get_pr_diff()

            # Extract suggestion text (everything after URL)
            query = cls.build_suggestion_query(pr_diff, comment_payload)

            await CodeGenerationHandler.generate_code_or_answer_query(
                query=query,  # Use suggestion as query
                codebase_path=repo_service.repo_dir,
                focus_files=None,
                focus_snippets=None,
                only_focus_code_chunks=False,
                use_llm_based_re_ranking=False,
                apply_diff=True,
                create_pr=True,
                source_branch=pr_model.source_branch(),
                destination_branch=pr_model.destination_branch(),
                operation=Feature.UPDATE_PR_SUGGESTION.value,  # Identifier for operation type
                repo_service=repo_service,
                scm_workspace_id=comment_payload.repo.workspace_id,
                pr_title_prefix="DD-330 ",
            )
        except Exception as e:
            logger.error(f"Error handling issue comment: {str(e)}")
            raise
        finally:
            repo_service.delete_local_repo()

    @classmethod
    def build_suggestion_query(cls, pr_diff, comment_payload: ChatRequest) -> str:
        user_suggestion = comment_payload.comment.raw[len("#suggestion") :].strip()
        return f"""
        User Query: {user_suggestion}
        Context lines where this Query was asked by user:
        <{comment_payload.comment.context_lines}>

        PR diff:
        <PR_DIFF>{pr_diff}</pr_diff>
        """

    @classmethod
    async def initialize_repo(cls, comment_payload: ChatRequest, vcs_type: str) -> BaseRepo:
        auth_handler = await get_vcs_auth_handler(comment_payload.repo.workspace_id, vcs_type)
        return await PRFactory.pr(
            vcs_type=vcs_type,
            repo_name=comment_payload.repo.repo_name,
            pr_id=comment_payload.repo.pr_id,
            workspace=comment_payload.repo.workspace,
            workspace_slug=comment_payload.repo.workspace_slug,
            workspace_id=comment_payload.repo.workspace_id,
            auth_handler=auth_handler,
        )
