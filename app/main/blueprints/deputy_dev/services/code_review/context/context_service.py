from torpedo import CONFIG

from app.common.services.chunking.chunking_manager import ChunkingManger
from app.common.services.embedding.managers.openai_embedding_manager import (
    OpenAIEmbeddingManager,
)
from app.common.services.pr.base_pr import BasePR
from app.common.services.repo.base_repo import BaseRepo
from app.common.services.repo.local_repo.managers.git_repo import GitRepo
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.services.tiktoken import TikToken
from app.common.utils.executor import process_executor
from app.main.blueprints.deputy_dev.services.atlassian.confluence.confluence_manager import (
    ConfluenceManager,
)
from app.main.blueprints.deputy_dev.services.atlassian.jira.jira_manager import (
    JiraManager,
)
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import append_line_numbers


class ContextService:
    def __init__(self, repo_service: BaseRepo, pr_service: BasePR):
        self.repo_service = repo_service
        self.pr_service = pr_service
        self.pr_title = None
        self.pr_description = None
        self.jira_manager = None
        self.jira_story = None
        self.confluence_doc_data = None
        self.relevant_chunk = None
        self.embedding_input_tokens = 0
        self.confluence_id = None
        self.issue_id = None
        self.pr_diff = None
        self.pr_diff_tokens = None
        self.pr_title_tokens = None
        self.pr_description_tokens = None
        self.pr_user_story_tokens = None
        self.confluence_doc_data_tokens = None
        self.tiktoken = TikToken()
        self.pr_status = None

    async def get_relevant_chunk(self):
        if not self.relevant_chunk:
            use_new_chunking = get_context_value("team_id") not in CONFIG.config["TEAMS_NOT_SUPPORTED_FOR_NEW_CHUNKING"]
            self.relevant_chunk, self.embedding_input_tokens = await ChunkingManger.get_relevant_chunks(
                query=self.pr_service.pr_commit_diff
                if get_context_value("pr_reviewable_on_commit")
                else self.pr_service.pr_diff,
                local_repo=GitRepo(self.repo_service.repo_dir),
                use_new_chunking=use_new_chunking,
                use_llm_re_ranking=False,
                embedding_manager=OpenAIEmbeddingManager,
                chunkable_files_with_hashes={},
                search_type=SearchTypes.NATIVE,
                process_executor=process_executor,
            )
        return self.relevant_chunk

    def get_pr_title(self):
        if not self.pr_title:
            self.pr_title = self.pr_service.pr_model().title()
            self.pr_title_tokens = self.tiktoken.count(self.pr_title)
        return self.pr_title

    def get_pr_description(self):
        if not self.pr_description:
            self.pr_description = self.pr_service.pr_model().description()
            self.pr_description_tokens = self.tiktoken.count(self.pr_description)
        return self.pr_description

    async def get_pr_diff(self, append_line_no_info=False):
        if not self.pr_diff:
            self.pr_diff = await self.pr_service.get_effective_pr_diff()
            self.pr_diff_tokens = self.tiktoken.count(self.pr_diff)
        if append_line_no_info:
            return append_line_numbers(self.pr_diff)
        else:
            return self.pr_diff

    async def get_user_story(self):
        if self.jira_story:
            return self.jira_story
        self.jira_manager = JiraManager(issue_id=self.get_issue_id())
        self.jira_story = await self.jira_manager.get_description_text()
        self.pr_user_story_tokens = self.tiktoken.count(self.jira_story)
        return self.jira_story

    async def get_confluence_doc(self):
        if self.confluence_doc_data:
            return self.confluence_doc_data
        if not self.jira_manager:
            return ""
        self.confluence_id = await self.jira_manager.get_confluence_link_attached()
        if self.confluence_id:
            self.confluence_doc_data = await ConfluenceManager(document_id=self.confluence_id).get_description_text()
            self.confluence_doc_data_tokens = self.tiktoken.count(self.confluence_doc_data)
        return self.confluence_doc_data

    def get_confluence_id(self):
        return self.confluence_id

    def get_issue_id(self) -> str:
        if not self.issue_id:
            self.issue_id = self.pr_service.pr_details.issue_id
        return self.issue_id

    def get_pr_status(self):
        if not self.pr_status:
            self.pr_status = self.pr_service.pr_model().scm_state()
        return self.pr_status
