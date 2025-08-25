from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import toml
from deputydev_core.utils.context_vars import get_context_value


class SettingHelper:
    DD_LEVEL_SETTINGS = toml.load(Path("./settings.toml"))
    PREDEFINED_AGENTS_IDS_AND_NAMES = {
        setting["agent_id"]: name for name, setting in DD_LEVEL_SETTINGS["code_review_agent"]["agents"].items()
    }
    REPO_SPECIFIC_KEYS = ["app"]

    @classmethod
    def merge_setting(cls, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges the override configuration into the base configuration.

        Parameters:
        - base_config (dict): The base configuration to be updated.
        - override_config (dict): The configuration with overriding values.

        Returns:
        - dict: The merged configuration.
        """
        if not override_config:
            return base_config

        for key, base_value in base_config.items():
            # Skip if the key does not exist or is None in the override config
            if key not in override_config or override_config[key] is None:
                continue

            # Recursive merging for nested dictionaries
            if isinstance(base_value, dict):
                if key == "agents":
                    base_config[key] = cls._merge_agents(base_value, override_config[key])
                else:
                    base_config[key] = cls.merge_setting(base_value, override_config[key])

            # Overriding simple boolean flags based on specific keys
            elif key in ["enable", "is_override"]:
                if base_config.get("is_override", True):
                    base_config[key] = override_config[key]

            # Union of lists for inclusion and exclusion settings
            elif key in ["exclusions", "inclusions"]:
                base_config[key] = list(set(base_value) | set(override_config[key]))

            # Default behavior for other keys
            else:
                base_config[key] = override_config[key]

        return base_config

    @classmethod
    def _merge_agents(cls, base_agents: Dict[str, Any], override_agents: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges agent configurations from the override into the base agents.

        Parameters:
        - base_agents (dict): The base agent configurations.
        - override_agents (dict): The overriding agent configurations.

        Returns:
        - dict: The merged agent configurations.
        """
        # Mapping of agent IDs to agent names in the base agents
        base_agent_ids = {agent_setting["agent_id"]: agent_name for agent_name, agent_setting in base_agents.items()}

        for key, override_value in override_agents.items():
            agent_id = override_value["agent_id"]

            # If agent ID exists in the base agents, merge the configurations
            if agent_id in base_agent_ids:
                base_agent_name = base_agent_ids[agent_id]
                base_agents[key] = cls.merge_setting(base_agents[base_agent_name], override_value)
                # Remove the old agent name if the new name differs
                if key != base_agent_name:
                    del base_agents[base_agent_name]
            else:
                # Add new agent configurations if agent ID is not in base agents
                base_agents[key] = override_value

            # Mark the agent as custom if it is not predefined
            base_agents[key]["is_custom_agent"] = agent_id not in cls.PREDEFINED_AGENTS_IDS_AND_NAMES

        return base_agents

    @staticmethod
    def agent_data_by_id(agents: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        agents_by_id = {
            data["agent_id"]: {"agent_name": agent_name, "display_name": data.get("display_name", "")}
            for agent_name, data in agents.items()
        }
        return agents_by_id

    @classmethod
    def agents_analytics_info_recursive(
        cls, level_agents_list: List[Dict[str, Any]], combined_agents: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if combined_agents is None:
            combined_agents = {}

        if not level_agents_list:
            return combined_agents

        current_level_agents = level_agents_list[0]

        if current_level_agents:
            for agent_name, agent_info in current_level_agents.items():
                agent_id = agent_info["agent_id"]
                if agent_id in combined_agents:
                    combined_agents[agent_id]["agent_name"] = agent_name
                    combined_agents[agent_id]["display_name"] = agent_info.get("display_name") or combined_agents[
                        agent_id
                    ].get("display_name", "")
                    combined_agents[agent_id]["severity"] = agent_info.get("severity") or combined_agents[agent_id].get(
                        "severity", ""
                    )
                else:
                    combined_agents[agent_id] = {
                        "agent_name": agent_name,
                        "display_name": agent_info.get("display_name") or "",
                        "severity": agent_info.get("severity"),
                    }

        return cls.agents_analytics_info_recursive(level_agents_list[1:], combined_agents)

    @staticmethod
    def chat_setting() -> Dict[str, Any]:
        setting = get_context_value("setting")
        return setting.get("chat", {}) if setting else {}

    @classmethod
    def global_code_review_agent_rules(cls) -> Dict[str, Any]:
        setting = get_context_value("setting")
        if not setting:
            return {}
        return setting["code_review_agent"]

    @classmethod
    def agents_settings(cls) -> Dict[str, Any]:
        setting = get_context_value("setting")
        if not setting:
            return {}
        return setting["code_review_agent"]["agents"]

    @classmethod
    def pre_defined_agents(cls) -> Dict[str, Any]:
        return cls.DD_LEVEL_SETTINGS["code_review_agent"]["agents"]

    @classmethod
    def summary_agent_id(cls) -> str:
        return cls.DD_LEVEL_SETTINGS["pr_summary"]["agent_id"]

    @classmethod
    def summary_agent_setting(cls) -> Dict[str, Any]:
        setting = get_context_value("setting")
        if not setting:
            return {}
        return setting["pr_summary"]

    @classmethod
    def agents(cls, setting: Dict[str, Any]) -> Dict[str, Any]:
        if setting:
            return setting.get("code_review_agent", {}).get("agents") or {}
        return {}

    @classmethod
    def agents_analytics_info(
        cls, dd_agents: Dict[str, Any], team_agents: Dict[str, Any], repo_agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        return cls.agents_analytics_info_recursive([dd_agents, team_agents, repo_agents])

    @classmethod
    def dd_level_settings(cls) -> Dict[str, Any]:
        return cls.DD_LEVEL_SETTINGS

    @classmethod
    def get_uuid_wise_agents(cls) -> Dict[str, Any]:
        setting = get_context_value("setting")
        agent_setting = setting["code_review_agent"]["agents"]
        pr_summary_setting = setting["pr_summary"]
        agents = {}
        for agent_name, agent_data in agent_setting.items():
            agent_data = {"agent_name": agent_name, **agent_data}
            agents[str(agent_data["agent_id"])] = agent_data
        agents[cls.summary_agent_id()] = {"agent_name": "pr_summary", **pr_summary_setting}
        return agents

    @classmethod
    def get_agent_inclusion_exclusions(cls, agent_id: Optional[str] = None) -> Tuple[List[str], List[str]]:
        setting = get_context_value("setting")
        global_exclusions = setting["code_review_agent"]["exclusions"] or []
        global_inclusions = setting["code_review_agent"]["inclusions"] or []
        if agent_id == cls.summary_agent_id():
            return list(global_inclusions), list(global_exclusions)
        else:
            agents = cls.get_uuid_wise_agents()
            if agent_id:
                inclusions = set(global_inclusions) | set(agents[agent_id].get("inclusions", []))
                exclusions = set(global_exclusions) | set(agents[agent_id].get("exclusions", []))
                return list(inclusions), list(exclusions)
            else:
                return list(global_inclusions), list(global_exclusions)

    @classmethod
    def agent_id_by_custom_name(cls, agent_name: str) -> str:
        agent_settings = cls.agents_settings()
        return agent_settings[agent_name]["agent_id"]

    @classmethod
    def predefined_name_to_custom_name(cls, agent_name: str) -> str:
        pre_defined_agents = cls.pre_defined_agents()
        if agent_name in pre_defined_agents:
            agent_id = pre_defined_agents[agent_name]["agent_id"]
            uuid_wise_agents = cls.get_uuid_wise_agents()
            return uuid_wise_agents[agent_id]["agent_name"]
        else:
            return agent_name

    @classmethod
    def custom_name_to_predefined_name(cls, agent_name: str) -> str:
        # In case of custom agent predefined_name will be same as custom agent
        all_agents = cls.agents_settings()
        if all_agents[agent_name]["is_custom_agent"]:
            return agent_name
        else:
            return cls.PREDEFINED_AGENTS_IDS_AND_NAMES[all_agents[agent_name]["agent_id"]]

    @classmethod
    def predefined_name_by_id(cls, agent_id: str) -> str:
        return cls.PREDEFINED_AGENTS_IDS_AND_NAMES.get(agent_id)

    @classmethod
    def custom_name_by_id(cls, agent_id: str) -> str:
        agents_settings = cls.get_uuid_wise_agents()
        return agents_settings[agent_id]["agent_name"]

    @classmethod
    def agent_setting_by_name(cls, agent_name: str) -> Dict[str, Any]:
        return cls.agents_settings().get(agent_name, {})

    @classmethod
    def agents_setting_by_agent_uuid(cls) -> Dict[str, Any]:
        agent_settings = cls.agents_settings()
        agents_by_agent_uuid = {}
        for agent_name, agent_data in agent_settings.items():
            agents_by_agent_uuid[agent_data["agent_id"]] = {**agent_data, "agent_name": agent_name}
        return agents_by_agent_uuid

    @classmethod
    def remove_repo_specific_setting(cls, setting: Dict[str, Any]) -> Dict[str, Any]:
        if setting:
            for key in cls.REPO_SPECIFIC_KEYS:
                if setting.get(key):
                    for nested_key in setting[key]:
                        setting[key][nested_key] = None
        return setting
