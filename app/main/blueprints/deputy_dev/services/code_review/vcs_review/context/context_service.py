from typing import Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.chunking.chunker.handlers.non_vector_db_chunker import (
    NonVectorDBChunker,
)
from deputydev_core.services.chunking.chunking_manager import ChunkingManger
from deputydev_core.services.repo.local_repo.managers.git_repo_service import GitRepo
from deputydev_core.services.search.dataclasses.main import SearchTypes
from deputydev_core.services.tiktoken import TikToken
from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.constants.constants import MAX_RELEVANT_CHUNKS
from app.backend_common.services.embedding.openai_embedding_manager import (
    OpenAIEmbeddingManager,
)
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.utils.app_utils import safe_index
from app.backend_common.utils.executor import process_executor
from app.backend_common.utils.formatting import append_line_numbers
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.services.atlassian.confluence.confluence_manager import (
    ConfluenceManager,
)
from app.main.blueprints.deputy_dev.services.atlassian.jira.jira_manager import (
    JiraManager,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.utils import is_path_included


class ContextService:
    def __init__(self, repo_service: BaseRepo, pr_service: BasePR, pr_diff_handler: PRDiffHandler) -> None:
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
        self.pr_diff_handler = pr_diff_handler

    async def get_relevant_chunk(self) -> List[ChunkInfo]:
        use_new_chunking = get_context_value("team_id") not in CONFIG.config["TEAMS_NOT_SUPPORTED_FOR_NEW_CHUNKING"]
        local_repo = GitRepo(self.repo_service.repo_dir)
        chunker = NonVectorDBChunker(
            local_repo=local_repo,
            process_executor=process_executor,
            use_new_chunking=use_new_chunking,
        )
        relevant_chunk, self.embedding_input_tokens, _ = await ChunkingManger.get_relevant_chunks(
            query=await self.pr_diff_handler.get_effective_pr_diff(),
            local_repo=local_repo,
            embedding_manager=OpenAIEmbeddingManager(),
            chunkable_files_with_hashes={},
            search_type=SearchTypes.NATIVE,
            process_executor=process_executor,
            chunking_handler=chunker,
            max_chunks_to_return=CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"],
        )
        return relevant_chunk

    # TODO: Add type hints for the return value without Any
    async def agent_wise_relevant_chunks(self) -> Dict[str, List[ChunkInfo]]:  # noqa: C901
        """
        Retrieves agent-wise relevant chunks by filtering and mapping ranked snippets to agents
        based on inclusion/exclusion rules. Avoids saving duplicate chunks to optimize memory usage.

        Instead of storing the same snippet multiple times for different agents,
        the snippets are stored once in code_snippet_list. Agents only store references (indices)
        to these snippets in relevant_chunks_mapping.

        Returns:
        - dict: A dictionary containing the following keys:
            - "relevant_chunks_mapping" (dict): Mapping of agent IDs to the indices of relevant code snippets.
            - "relevant_chunks" (list): A list of unique code snippets relevant to the agents.
            - "comment_validation_relevant_chunks_mapping" (list): Indices of snippets for comment validation agents.
        """
        if not self.relevant_chunk:
            # Get the ranked list of relevant code snippets
            ranked_snippets_list = await self.get_relevant_chunk()
            agents = SettingService.helper.get_uuid_wise_agents()  # Retrieve all agents
            remaining_agents = len(agents)  # Count of agents yet to be fulfilled
            code_snippet_list: List[ChunkInfo] = []  # Unique list of code snippets to avoid duplicates
            comment_validation_relevant_chunks_mapping = []  # Indices of snippets relevant to comment validation agents

            # Initialize a mapping of agent IDs to relevant chunk indices
            relevant_chunks_mapping = {agent_id: [] for agent_id, agent_data in agents.items() if agent_data["enable"]}

            for snippet in ranked_snippets_list:
                if remaining_agents == 0:
                    break  # Exit early if all agents have enough chunks

                path = snippet.denotation  # Path of the current snippet

                for agent_id in relevant_chunks_mapping:
                    # Skip agents that already have the required number of chunks
                    if len(relevant_chunks_mapping[agent_id]) >= MAX_RELEVANT_CHUNKS:
                        continue

                    # Get inclusion/exclusion rules for the agent
                    inclusions, exclusions = SettingService.helper.get_agent_inclusion_exclusions(agent_id)

                    # Check if the snippet path is relevant for the agent
                    if is_path_included(path, exclusions, inclusions):
                        # Check if the snippet already exists in the code_snippet_list
                        index = safe_index(code_snippet_list, snippet)
                        if index is not None:
                            # If it exists, append its index to the agent's mapping
                            relevant_chunks_mapping[agent_id].append(index)
                        else:
                            # If it doesn't exist, add it to the list and map it to the agent
                            if agent_id != SettingService.helper.summary_agent_id():
                                comment_validation_relevant_chunks_mapping.append(len(code_snippet_list))
                            relevant_chunks_mapping[agent_id].append(len(code_snippet_list))
                            code_snippet_list.append(snippet)

                        # Decrement the counter when the agent reaches the chunk limit
                        if len(relevant_chunks_mapping[agent_id]) == MAX_RELEVANT_CHUNKS:
                            remaining_agents -= 1

                            # Exit early if all agents are fulfilled
                            if remaining_agents == 0:
                                break

            # Save the results to the instance variable
            self.relevant_chunk = {
                "relevant_chunks_mapping": relevant_chunks_mapping,
                "relevant_chunks": code_snippet_list,
                "comment_validation_relevant_chunks_mapping": comment_validation_relevant_chunks_mapping,
            }

        return self.relevant_chunk

    def get_pr_title(self) -> str:
        if not self.pr_title:
            self.pr_title = self.pr_service.pr_model().title()
            self.pr_title_tokens = self.tiktoken.count(self.pr_title)
        return self.pr_title

    def get_pr_description(self) -> str:
        if not self.pr_description:
            self.pr_description = self.pr_service.pr_model().description()
            self.pr_description_tokens = self.tiktoken.count(self.pr_description)
        return self.pr_description

    async def get_pr_diff(
        self, append_line_no_info: bool = False, operation: str = "code_review", agent_id: Optional[str] = None
    ) -> str:
        pr_diff = await self.pr_diff_handler.get_effective_pr_diff(operation, agent_id)
        self.pr_diff_tokens = await self.pr_diff_handler.pr_diffs_token_counts(operation)
        if append_line_no_info:
            return append_line_numbers(pr_diff)
        else:
            return pr_diff

    async def get_user_story(self) -> str:
        if self.jira_story:
            return self.jira_story
        self.jira_manager = JiraManager(issue_id=self.get_issue_id())
        self.jira_story = await self.jira_manager.get_description_text()
        self.pr_user_story_tokens = self.tiktoken.count(self.jira_story)
        return self.jira_story

    async def get_confluence_doc(self) -> str:
        if self.confluence_doc_data:
            return self.confluence_doc_data
        if not self.jira_manager:
            return ""
        self.confluence_id = await self.jira_manager.get_confluence_link_attached()
        if self.confluence_id:
            self.confluence_doc_data = await ConfluenceManager(document_id=self.confluence_id).get_description_text()
            self.confluence_doc_data_tokens = self.tiktoken.count(self.confluence_doc_data)
        return self.confluence_doc_data

    def get_confluence_id(self) -> str:
        return self.confluence_id

    def get_issue_id(self) -> str:
        if not self.issue_id:
            self.issue_id = self.pr_service.pr_details.issue_id
        return self.issue_id

    def get_pr_status(self) -> str:
        if not self.pr_status:
            self.pr_status = self.pr_service.pr_model().scm_state()
        return self.pr_status
