from app.common.utils.app_utils import safe_index
from app.main.blueprints.deputy_dev.services.setting_service import SettingService
from app.main.blueprints.deputy_dev.services.workspace.context_vars import get_context_value
from app.main.blueprints.deputy_dev.utils import ignore_files
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken


class PRDiffService:
    def __init__(self, pr_diff):
        self.pr_diff = pr_diff
        self.pr_diff_mappings = {}
        self.pr_diffs = []
        self.tiktoken = TikToken()

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
            self.summary_pr_diff_mapping()
        elif operation == "chat":
            self.chat_pr_diff_mapping()

    def map_complete_pr_diff(self):
        self.pr_diff_mappings["complete_pr_diff"] = 0
        self.pr_diffs.append(self.pr_diff)

    def summary_pr_diff_mapping(self):
        pr_summary_diff = self.exclude_pr_diff(operation="pr_summary")
        agent_id = SettingService.summary_agent_id()
        self.map_pr_diff(key=agent_id, extracted_pr_diff=pr_summary_diff)

    def code_review_agents_pr_diff_mapping(self):
        uuid_wise_agents = SettingService.get_agents_by_uuid()
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
            code_review_agent = settings.get("code_review_agent", {})
            agents = SettingService.get_agents_by_uuid()
            if agent_id:
                inclusions = set(code_review_agent.get("inclusions", [])) | set(agents[agent_id].get("inclusions", []))
                exclusions = set(code_review_agent.get("exclusions", [])) | set(agents[agent_id].get("exclusions", []))
            else:
                inclusions = set(code_review_agent.get("inclusions", []))
                exclusions = set(code_review_agent.get("exclusions", []))
        elif operation == "chat":
            chat_setting = settings["chat"]
            inclusions = chat_setting.get("inclusions", [])
            exclusions = chat_setting.get("exclusions", [])
        elif operation == "pr_summary":
            summary_setting = settings["pr_summary"]
            inclusions = summary_setting.get("inclusions", [])
            exclusions = summary_setting.get("exclusions", [])
        return ignore_files(self.pr_diff, list(exclusions), list(inclusions))

    def pr_diffs_token_counts(self, operation="code_review"):
        pr_diff_token_count = {}
        if not self.pr_diff_mappings:
            self.get_pr_diff_mappings(operation)
        if operation == "chat":
            diff_index = self.pr_diff_mappings.get("chat")
            pr_diff_token_count["chat"] = self.tiktoken.count(self.pr_diffs[diff_index])
        else:
            for agent_id, agent_data in self.pr_diff_mappings.items():
                diff_index = self.pr_diff_mappings[agent_id]
                pr_diff_token_count[agent_id] = self.tiktoken.count(self.pr_diffs[diff_index])
        return pr_diff_token_count
