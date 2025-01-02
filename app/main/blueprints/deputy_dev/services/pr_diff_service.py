from app.common.utils.app_utils import get_token_count, safe_index
from app.main.blueprints.deputy_dev.constants.repo import PR_NOT_FOUND
from app.main.blueprints.deputy_dev.services.setting_service import SettingService
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import ignore_files


class PRDiffService:
    # TODO: add docstrings in functions of this class
    def __init__(self, pr_diff):
        self.pr_diff = pr_diff
        self.pr_diff_mappings = {}
        self.pr_diffs = []

    def get_pr_diff(self, operation="code_review", agent_id=None):
        if not self.pr_diff_mappings:
            self.get_pr_diff_mappings(operation)
        if operation == "chat":
            diff_index = self.pr_diff_mappings.get("chat")
        else:
            if agent_id:
                diff_index = self.pr_diff_mappings[agent_id]
            else:
                diff_index = self.pr_diff_mappings["code_review"]
        return self.pr_diffs[diff_index]

    def get_pr_diff_mappings(self, operation):
        # benchmarked this function searching a string of length 10k in a list of 10 items
        # where each string is almost equal and of around 10k len take 10 microseconds.
        self.map_complete_pr_diff()
        if operation == "code_review":
            self.code_review_global_pr_diff_mapping()
            self.code_review_agents_pr_diff_mapping()
        elif operation == "chat":
            self.chat_pr_diff_mapping()

    def map_complete_pr_diff(self):
        self.pr_diff_mappings["complete_pr_diff"] = 0
        self.pr_diffs.append(self.pr_diff)

    # def summary_pr_diff_mapping(self):
    #     pr_summary_diff = self.exclude_pr_diff(operation="pr_summary")
    #     agent_id = SettingService.summary_agent_id()
    #     self.map_pr_diff(key=agent_id, extracted_pr_diff=pr_summary_diff)

    def code_review_agents_pr_diff_mapping(self):
        uuid_wise_agents = SettingService.get_uuid_wise_agents()
        for agent_id in uuid_wise_agents:
            agent_pr_diff = self.exclude_pr_diff(agent_id=agent_id)
            self.map_pr_diff(key=agent_id, extracted_pr_diff=agent_pr_diff)

    def code_review_global_pr_diff_mapping(self):
        global_pr_diff = self.exclude_pr_diff()
        self.map_pr_diff(key="code_review", extracted_pr_diff=global_pr_diff)

    def chat_pr_diff_mapping(self):
        chat_diff = self.exclude_pr_diff(operation="chat")
        self.map_pr_diff(key="chat", extracted_pr_diff=chat_diff)

    def map_pr_diff(self, key, extracted_pr_diff):
        index = safe_index(self.pr_diffs, extracted_pr_diff, -1)
        if index != -1:
            self.pr_diff_mappings[key] = index
        else:
            self.pr_diffs.append(extracted_pr_diff)
            self.pr_diff_mappings[key] = len(self.pr_diffs) - 1

    def exclude_pr_diff(self, operation="code_review", agent_id=None):
        """
        - operations can be code_review, chat, summary
        - in case of code_review agent_id is mandatory
        """
        settings = get_context_value("setting") or {}
        inclusions, exclusions = [], []
        if operation == "code_review":
            inclusions, exclusions = SettingService.get_agent_inclusion_exclusions(agent_id)
        elif operation == "chat":
            # TODO: Need to confirm that we want exclusions/inclusions in chat or not
            chat_setting = settings["chat"]
            inclusions = chat_setting.get("inclusions", [])
            exclusions = chat_setting.get("exclusions", [])
        return ignore_files(self.pr_diff, list(exclusions), list(inclusions))

    def pr_diffs_token_counts(self, operation="code_review"):
        pr_diff_token_count = {}
        if operation == "chat":
            pr_diff_token_count["chat"] = self.count_pr_diff_tokens(operation)
        else:
            for agent_id in SettingService.get_uuid_wise_agents():
                pr_diff_token_count[agent_id] = self.count_pr_diff_tokens(operation, agent_id)
        return pr_diff_token_count

    def count_pr_diff_tokens(self, operation="code_review", agent_id=None):
        pr_diff = self.get_pr_diff(operation, agent_id)
        if pr_diff and pr_diff != PR_NOT_FOUND:
            return get_token_count(pr_diff)
        else:
            return 0

    def pr_diffs_token_counts_agent_name_wise(self, operation="code_review"):
        pr_diff_token_count = self.pr_diffs_token_counts(operation)
        if operation == "code_review":
            pr_diff_token_count_agent_name_wise = {}
            agents_uuid_wise = SettingService.get_uuid_wise_agents()
            for agent_id, token_count in pr_diff_token_count.items():
                agent_name = agents_uuid_wise[agent_id]["agent_name"]
                pr_diff_token_count_agent_name_wise[agent_name] = token_count
            return pr_diff_token_count_agent_name_wise
        else:
            return pr_diff_token_count
