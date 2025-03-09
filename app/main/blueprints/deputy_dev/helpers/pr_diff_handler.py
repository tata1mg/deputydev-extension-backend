from typing import Any, Dict

from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.constants.constants import LARGE_PR_DIFF, PR_NOT_FOUND
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.utils.app_utils import get_token_count, safe_index
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.utils import ignore_files


class PRDiffHandler:
    """
    Service that manages the PR diffs and their mappings, and provides operations for retrieving and processing them.
    """

    def __init__(self, pr_service: BasePR):
        """
        Initializes the PRDiffService with the provided PR diff.

        :param pr_service: An instance of a PR service (implementing BasePR)
        :type pr_service: BasePR
        """
        self.pr_service = pr_service
        self.pr_diff = None  # Original PR diff content
        self.pr_diff_mappings = {}  # Maps operation/agent to indices in pr_diffs
        self.pr_diffs = []  # List of unique PR diffs for efficient memory usage

    async def get_effective_pr_diff(self, operation: str = "code_review", agent_id: str = None) -> str:
        """
        Retrieves the PR diff based on the operation and optionally the agent ID.

        :param operation: The operation type (e.g., "code_review", "chat").
        :type operation: str
        :param agent_id: The agent ID for "code_review" operation (optional).
        :type agent_id: str, optional

        :return: The corresponding PR diff.
        :rtype: str
        """
        if not self.pr_diff:
            self.pr_diff = await self.pr_service.get_commit_diff_or_pr_diff()
        # If no mappings exist, populate them
        if not self.pr_diff_mappings:
            self.set_pr_diff_mappings(operation)

        # Choose the correct PR diff based on the operation and agent ID
        if operation == "chat":
            diff_index = self.pr_diff_mappings.get("chat")
        else:
            if agent_id:
                diff_index = self.pr_diff_mappings[agent_id]
            else:
                diff_index = self.pr_diff_mappings["global_diff"]

        # Return the corresponding PR diff from the list
        return self.pr_diffs[diff_index]

    def set_pr_diff_mappings(self, operation: str):
        """
        Populates the mappings for the PR diffs based on the operation.

        :param operation: The operation type (e.g., "code_review", "chat").
        :type operation: str
        """
        # Map the complete PR diff first
        self.map_complete_pr_diff()

        # Based on the operation, map the relevant PR diffs
        if operation == "code_review":
            self.code_review_global_pr_diff_mapping()  # Global mapping for code review
            self.code_review_agents_pr_diff_mapping()  # Agent-specific mappings for code review
        elif operation == "chat":
            self.chat_pr_diff_mapping()  # Mapping for chat operation

    def map_complete_pr_diff(self):
        """
        Maps the complete PR diff to the mappings.
        """
        # Add the complete PR diff to the mappings
        self.pr_diff_mappings["complete_pr_diff"] = 0
        self.pr_diffs.append(self.pr_diff)

    def code_review_agents_pr_diff_mapping(self):
        """
        Maps the PR diffs for each agent in the code review operation.
        """
        # Fetch the list of agents by UUID
        uuid_wise_agents = SettingService.helper.get_uuid_wise_agents()

        # For each agent, process the PR diff and map it
        for agent_id in uuid_wise_agents:
            agent_pr_diff = self.exclude_pr_diff(agent_id=agent_id)  # Exclude agent-specific diffs
            self.map_pr_diff(key=agent_id, extracted_pr_diff=agent_pr_diff)  # Map the extracted diff to the agent

    def code_review_global_pr_diff_mapping(self):
        """
        Maps the global PR diff for the code review operation.
        """
        # Get the global PR diff
        global_pr_diff = self.exclude_pr_diff()
        self.map_pr_diff(key="global_diff", extracted_pr_diff=global_pr_diff)  # Map the global diff

    def chat_pr_diff_mapping(self):
        """
        Maps the PR diff for the chat operation.
        """
        # Get the PR diff specific to the chat operation
        chat_diff = self.exclude_pr_diff(operation="chat")
        self.map_pr_diff(key="chat", extracted_pr_diff=chat_diff)  # Map the chat diff

    def map_pr_diff(self, key: str, extracted_pr_diff: str):
        """
        Maps the extracted PR diff to the provided key.

        :param key: The key for mapping.
        :type key: str
        :param extracted_pr_diff: The extracted PR diff.
        :type extracted_pr_diff: str
        """
        # Find the index of the extracted PR diff, if it exists
        index = safe_index(self.pr_diffs, extracted_pr_diff, -1)

        if index != -1:
            # If the PR diff already exists, map it to the key
            self.pr_diff_mappings[key] = index
        else:
            # Otherwise, add it to the list and map it
            self.pr_diffs.append(extracted_pr_diff)
            self.pr_diff_mappings[key] = len(self.pr_diffs) - 1

    def exclude_pr_diff(self, operation: str = "code_review", agent_id: str = None) -> str:
        """
        Excludes certain lines from the PR diff based on the operation and agent ID.

        :param operation: The operation type (e.g., "code_review", "chat").
        :type operation: str
        :param agent_id: The agent ID for "code_review" operation (optional).
        :type agent_id: str, optional

        :return: The filtered PR diff.
        :rtype: str
        """
        # Get the settings context
        settings = get_context_value("setting") or {}
        inclusions, exclusions = [], []

        # Handle different operations (code_review or chat)
        if operation == "code_review":
            inclusions, exclusions = SettingService.helper.get_agent_inclusion_exclusions(agent_id)
        elif operation == "chat":
            chat_setting = settings["chat"]
            inclusions = chat_setting.get("inclusions", [])
            exclusions = chat_setting.get("exclusions", [])

        # Return the filtered PR diff with exclusions and inclusions
        return ignore_files(self.pr_diff, list(exclusions), list(inclusions))

    async def pr_diffs_token_counts(self, operation: str = "code_review") -> Dict[str, int]:
        """
        Counts the number of tokens in the PR diffs for each agent or operation.

        :param operation: The operation type (e.g., "code_review", "chat").
        :type operation: str

        :return: A dictionary with the token counts.
        :rtype: dict
        """
        pr_diff_token_count = {}

        # Count tokens for each agent or operation
        if operation == "chat":
            pr_diff_token_count["chat"] = await self.count_pr_diff_tokens(operation)
        else:
            for agent_id in SettingService.helper.get_uuid_wise_agents():
                pr_diff_token_count[agent_id] = await self.count_pr_diff_tokens(operation, agent_id)

        return pr_diff_token_count

    async def count_pr_diff_tokens(self, operation: str = "code_review", agent_id: str = None) -> int:
        """
        Counts the number of tokens in a specific PR diff.

        :param operation: The operation type (e.g., "code_review", "chat").
        :type operation: str
        :param agent_id: The agent ID for "code_review" operation (optional).
        :type agent_id: str, optional

        :return: The number of tokens in the PR diff.
        :rtype: int
        """
        # Retrieve the correct PR diff
        pr_diff = await self.get_effective_pr_diff(operation, agent_id)

        # Return the token count if the PR diff is found
        if pr_diff and pr_diff != PR_NOT_FOUND and pr_diff != LARGE_PR_DIFF:
            return get_token_count(pr_diff)
        else:
            return 0

    async def pr_diffs_token_counts_agent_name_wise(self, operation: str = "code_review") -> Dict[str, Any]:
        """
        Counts the PR diff tokens and maps them to agent names.

        :param operation: The operation type (e.g., "code_review", "chat").
        :type operation: str

        :return: A dictionary with agent names and their corresponding token counts.
        :rtype: dict
        """
        # Get the token counts for the specified operation
        pr_diff_token_count = await self.pr_diffs_token_counts(operation)

        # If the operation is "code_review", map the counts to agent names
        if operation == "code_review":
            pr_diff_token_count_agent_name_wise = {}
            agents_uuid_wise = SettingService.helper.get_uuid_wise_agents()
            for agent_id, token_count in pr_diff_token_count.items():
                agent_name = agents_uuid_wise[agent_id]["agent_name"]
                pr_diff_token_count_agent_name_wise[agent_name] = token_count
            return pr_diff_token_count_agent_name_wise
        else:
            return pr_diff_token_count

    async def get_pr_diff_token_count(self, operation="code_review") -> Dict[str, Any]:
        return await self.pr_diffs_token_counts_agent_name_wise(operation)
