from app.common.utils.context_vars import get_context_value


class SettingHelper:
    DD_LEVEL_SETTINGS = toml.load(Path("./settings.toml"))
    PREDEFINED_AGENTS_IDS_AND_NAMES = {
        setting["agent_id"]: name for name, setting in DD_LEVEL_SETTINGS["code_review_agent"]["agents"].items()
    }

    @classmethod
    def merge_setting(cls, base_config, override_config):
        if not override_config:
            return base_config

        for key, base_value in base_config.items():
            if key not in override_config or override_config[key] is None:
                continue

            if isinstance(base_value, dict):
                if key == "agents":
                    base_config[key] = cls._merge_agents(base_value, override_config[key])
                else:
                    base_config[key] = cls.merge_setting(base_value, override_config[key])

            elif key == "enable" or key == "is_override":
                if base_config.get("is_override", True):
                    base_config[key] = override_config[key]
            elif key in ["exclusions", "inclusions"]:
                base_config[key] = list(set(base_value) | set(override_config[key]))
            else:
                base_config[key] = override_config[key]

        return base_config

    @classmethod
    def _merge_agents(cls, base_agents, override_agents):
        base_agent_ids = {agent_setting["agent_id"]: agent_name for agent_name, agent_setting in base_agents.items()}
        for key, override_value in override_agents.items():
            agent_id = override_value["agent_id"]
            if agent_id in base_agent_ids:
                base_agent_name = base_agent_ids[agent_id]
                base_agents[key] = cls.merge_setting(base_agents[base_agent_name], override_value)
                if key != base_agent_name:
                    del base_agents[base_agent_name]
            else:
                base_agents[key] = override_value
            base_agents[key]["is_custom_agent"] = agent_id not in cls.PREDEFINED_AGENTS_IDS_AND_NAMES

        return base_agents

    @staticmethod
    def agent_data_by_id(agents):
        agents_by_id = {
            data["agent_id"]: {"agent_name": agent_name, "display_name": data.get("display_name", "")}
            for agent_name, data in agents.items()
        }
        return agents_by_id

    @classmethod
    def agents_analytics_info_recursive(cls, level_agents_list, combined_agents=None):
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
    def chat_setting():
        setting = get_context_value("setting")
        return setting.get("chat", {}) if setting else {}

    @classmethod
    def agents_settings(cls):
        setting = get_context_value("setting")
        return setting["code_review_agent"]["agents"]

    @classmethod
    def pre_defined_agents(cls):
        return cls.DD_LEVEL_SETTINGS["code_review_agent"]["agents"]

    @classmethod
    def summary_agent_id(cls):
        return cls.DD_LEVEL_SETTINGS["pr_summary"]["agent_id"]

    @classmethod
    def summary_agent_setting(cls):
        return cls.DD_LEVEL_SETTINGS["pr_summary"]

    @classmethod
    def agents(cls, setting):
        if setting:
            return setting.get("code_review_agent", {}).get("agents") or {}
        return {}

    @classmethod
    def agents_analytics_info(cls, dd_agents, team_agents, repo_agents):
        return cls.agents_analytics_info_recursive([dd_agents, team_agents, repo_agents])
