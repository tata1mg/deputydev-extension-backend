import re

from sanic.log import logger

from app.backend_common.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.constants.constants import Feature
from app.main.blueprints.deputy_dev.services.code_generation.code_generation_handler import (
    CodeGenerationHandler,
)
from app.main.blueprints.deputy_dev.services.webhook.issue_comment_webhook import (
    IssueCommentWebhook,
)
from app.main.blueprints.deputy_dev.utils import (
    get_vcs_auth_handler,
    update_payload_with_jwt_data,
)
from deputydev_core.utils.context_vars import get_context_value


class IssueCodeGenerationManager:
    DESTINATION_BRANCH_PATTERN = r"destination_branch:\s*([^\s\n]+)"  # branch:<branch_name> pattern
    SOURCE_BRANCH_PATTERN = r"source_branch:\s*([^\s\n]+)"  # branch:<branch_name> pattern
    QUERY_PATTERN = r"query:\s*([^\n]*(?:\n(?!branch:)[^\n]*)*)"
    CREATE_PR_COMMAND = "#create_pr"
    SUGGESTION_COMMAND = "#suggestion"
    PR_URL_PATTERN = r"(https?://[^\s]+)"

    @classmethod
    async def handle_issue_comment(cls, payload, query_params):
        """Handle code generation requests from issue comments"""

        logger.info(f"Issue comment payload: {payload}")
        logger.info(f"Issue comment query params {query_params}")

        payload = update_payload_with_jwt_data(query_params, payload)

        issue_comment_payload = await IssueCommentWebhook.parse_payload(payload)

        comment = issue_comment_payload.issue_comment.strip()
        command_type = cls.get_command_type(comment)

        repo_service = await cls.initialize_repo(issue_comment_payload, comment, command_type)

        try:
            _, is_repo_cloned = await repo_service.clone_repo()
            if not is_repo_cloned:
                logger.error("Failed to clone repository")
                return

            await cls.process_command(command_type, issue_comment_payload, repo_service)

        except Exception as e:
            logger.error(f"Error handling issue comment: {str(e)}")
            raise
        finally:
            repo_service.delete_local_repo()

    @classmethod
    async def process_command(cls, command_type: str, issue_comment_payload, repo_service):
        """Process the command based on its type"""
        comment_body = ""
        if command_type == cls.CREATE_PR_COMMAND:
            await cls.handle_create_pr(issue_comment_payload, repo_service)
            pr_url = get_context_value("pr_url")
            if pr_url:
                comment_body = f"✅ Pull Request created: {pr_url}"
            await repo_service.create_issue_comment(issue_id=issue_comment_payload.issue_id, comment=comment_body)
        elif command_type == cls.SUGGESTION_COMMAND:
            await cls.handle_suggestion(issue_comment_payload, repo_service)

    @classmethod
    async def handle_create_pr(cls, issue_comment_payload, repo_service):
        """Handle PR creation command"""
        destination_branch, source_branch = cls.parse_branches_form_comment(issue_comment_payload.issue_comment)

        response = await CodeGenerationHandler.generate_code_or_answer_query(  # noqa : F841
            query=issue_comment_payload.issue_description,  # Use issue description as query
            codebase_path=repo_service.repo_dir,
            focus_files=None,
            focus_snippets=None,
            only_focus_code_chunks=False,
            use_llm_based_re_ranking=False,
            apply_diff=False,
            create_pr=True,
            scm_workspace_id=issue_comment_payload.scm_workspace_id,
            destination_branch=destination_branch,
            source_branch=source_branch,
            operation=Feature.GENERATE_CODE.value,  # Identifier for operation type
            repo_service=repo_service,
            pr_title_prefix="DD-330 ",
        )

    @classmethod
    async def handle_suggestion(cls, issue_comment_payload, repo_service):
        """Handle suggestion command"""
        # Get PR details for branch information
        pr_model = repo_service.pr_model()

        # Extract suggestion text (everything after URL)
        suggestion = cls.extract_suggestion_text(issue_comment_payload.issue_comment)

        response = await CodeGenerationHandler.generate_code_or_answer_query(  # noqa : F841
            query=suggestion,  # Use suggestion as query
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
            scm_workspace_id=issue_comment_payload.scm_workspace_id,
            pr_title_prefix="DD-330 ",
        )

    @classmethod
    def get_command_type(cls, comment: str):
        if comment.startswith(cls.CREATE_PR_COMMAND):
            return cls.CREATE_PR_COMMAND
        elif comment.startswith(cls.SUGGESTION_COMMAND):
            return cls.SUGGESTION_COMMAND
        return None

    @classmethod
    def should_process_comment(cls, comment: str) -> bool:
        """Check if comment should trigger code generation"""
        return comment.lower().strip().startswith(cls.CREATE_PR_COMMAND)

    @classmethod
    def parse_branches_form_comment(cls, comment: str):
        """
        Parse issue description to extract query and branch information
        Returns tuple of (query, branch)
        """
        # Extract branch
        destination_branch = cls.extract_pattern_response(comment, cls.DESTINATION_BRANCH_PATTERN) or "master"
        source_branch = cls.extract_pattern_response(comment, cls.SOURCE_BRANCH_PATTERN)

        return destination_branch, source_branch

    @classmethod
    def extract_pattern_response(cls, text: str, matching_pattern) -> str:
        """Extract destination branch from issue description if specified"""
        branch_match = re.search(matching_pattern, text)
        return branch_match.group(1) if branch_match else None

    @classmethod
    async def initialize_repo(cls, issue_comment_payload, comment, command_type):
        pr_id = None
        branch_name = None

        if command_type == cls.CREATE_PR_COMMAND:
            # For create_pr, use destination branch as branch_name
            branch_name = cls.extract_pattern_response(comment, cls.DESTINATION_BRANCH_PATTERN)
        elif command_type == cls.SUGGESTION_COMMAND:
            # For suggestion, extract PR ID from URL
            # Pass branch as None and it will automatically be picked after fetching pr_details

            pr_url = re.search(cls.PR_URL_PATTERN, comment)
            if pr_url:
                pr_id = cls.extract_pr_id_from_url(pr_url.group(1))

        auth_handler = await get_vcs_auth_handler(
            issue_comment_payload.scm_workspace_id, issue_comment_payload.vcs_type
        )
        return await RepoFactory.repo(
            vcs_type=issue_comment_payload.vcs_type,
            repo_name=issue_comment_payload.repo_name,
            pr_id=pr_id,  # No PR yet
            workspace=issue_comment_payload.workspace,
            workspace_slug=issue_comment_payload.workspace_slug,
            workspace_id=issue_comment_payload.scm_workspace_id,
            auth_handler=auth_handler,
            branch_name=branch_name,
        )

    @classmethod
    def extract_pr_id_from_url(cls, url: str) -> str:
        match = re.search(r"/pull-requests/(\d+)", url)
        return match.group(1) if match else None

    @classmethod
    def extract_suggestion_text(cls, comment: str) -> str:
        url_match = re.search(cls.PR_URL_PATTERN, comment)
        if url_match:
            return comment[url_match.end() :].strip()
        return ""
