import copy
from pathlib import Path

import toml
from torpedo.exceptions import BadRequestException

from app.backend_common.services.repo.base_repo import BaseRepo
from app.common.constants.constants import (
    CUSTOM_PROMPT_CHAR_LIMIT,
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
)
from app.main.blueprints.deputy_dev.models.dao.postgres import Agents, Configurations, Repos
from app.common.utils.context_vars import (
    context_var,
    get_context_value,
    set_context_values,
)
from app.main.blueprints.deputy_dev.caches.repo_setting_cache import RepoSettingCache
from app.main.blueprints.deputy_dev.constants.constants import SettingLevel
from app.main.blueprints.deputy_dev.models.dao.postgres import Configurations
from app.main.blueprints.deputy_dev.utils import (
    get_workspace,
    update_payload_with_jwt_data,
)


class SettingService:
    DD_LEVEL_SETTINGS = toml.load(Path("./settings.toml"))
    PREDEFINED_AGENTS_IDS_AND_NAMES = {
        setting["agent_id"]: name for name, setting in DD_LEVEL_SETTINGS["code_review_agent"]["agents"].items()
    }
    repo_specific_keys = ["app"]

    def __init__(self, repo_service: BaseRepo, team_id=None, default_branch=None):
        self.repo_service = repo_service
        self.team_id = team_id
        self.default_branch = default_branch

    async def build(self):
        if "setting" in context_var.get():
            setting = get_context_value("setting")
            return setting
        self.default_branch = await self.repo_service.get_default_branch()
        repo_level_settings = await self.repo_level_settings()
        team_level_settings = await self.team_level_settings()
        team_level_settings = self.remove_repo_specific_setting(team_level_settings)
        base_settings = self.dd_level_settings()
        final_setting = copy.deepcopy(base_settings)
        final_setting = self.merge_setting(final_setting, team_level_settings)
        final_setting = self.merge_setting(final_setting, repo_level_settings)
        set_context_values(setting=final_setting)
        return final_setting

    @classmethod
    def validate_settings(cls, base_settings, override_settings):
        errors = {}
        error_message = cls.validate_types(base_settings, override_settings)
        if error_message:
            error_type = SettingErrorType.INVALID_SETTING.value
            errors[error_type] = f"""{SETTING_ERROR_MESSAGE[error_type]}{error_message}"""
            return errors, True
        errors.update(cls.validate_custom_prompts(override_settings))
        return errors, False

    @classmethod
    def validate_agents(cls, agents):
        for agent_name, agent_data in agents.items():
            if "agent_id" not in agent_data:
                agents.pop(agent_name)

    @classmethod
    def validate_types(cls, base_settings, override_settings, key_path=""):
        error = ""
        if not override_settings:
            return error
        for key, value in base_settings.items():
            current_path = f"{key_path}{key}"
            if key in override_settings and override_settings[key] is not None:
                if not isinstance(override_settings[key], type(value)):
                    error += f"Type of {current_path} should be {type(value).__name__}.\n"
                elif isinstance(value, dict):
                    error += cls.validate_types(value, override_settings[key], current_path + ".")
        return error

    @classmethod
    def validate_custom_prompts(cls, setting):
        errors = {}
        errors.update(cls._validate_agent_prompts(setting))
        errors.update(cls._validate_chat_prompt(setting))
        return errors

    @classmethod
    def _validate_agent_prompts(cls, setting):
        error, errors = "", {}
        agents_setting = setting.get("code_review_agent", {}).get("agents", {})
        for key, value in agents_setting.items():
            if value.get("custom_prompt") and len(value.get("custom_prompt")) > CUSTOM_PROMPT_CHAR_LIMIT:
                error += f"- {key} agent: {len(value.get('custom_prompt'))} characters.\n"
                value["custom_prompt"] = ""
        summary_custom_prompt = setting.get("pr_summary", {}).get("custom_prompt", "")
        if len(summary_custom_prompt) > CUSTOM_PROMPT_CHAR_LIMIT:
            error += f"- pr_summary agent: {len(summary_custom_prompt)} characters."
            setting["pr_summary"]["custom_prompt"] = ""
        if error:
            error_type = SettingErrorType.CUSTOM_PROMPT_LENGTH_EXCEED.value
            errors[error_type] = f"""{SETTING_ERROR_MESSAGE[error_type]}{error}"""
        return errors

    @classmethod
    def _validate_chat_prompt(cls, setting):
        error, errors = "", {}
        chat_custom_prompt = setting.get("chat", {}).get("custom_prompt", "")
        if len(chat_custom_prompt) > CUSTOM_PROMPT_CHAR_LIMIT:
            error_type = SettingErrorType.INVALID_CHAT_SETTING.value
            error = f", provided prompt length is {len(chat_custom_prompt)}."
            setting["chat"]["custom_prompt"] = ""
            errors[error_type] = f"{SETTING_ERROR_MESSAGE[error_type]}{error}"
        return errors

    async def repo_level_settings(self):
        """
        Asynchronously retrieves repository-level settings, utilizing caching to reduce
        database queries. Handles various cache states and potential errors gracefully.

        :return: A dictionary representing the repository settings, or an empty dictionary
                 if no settings exist or an error occurred.
        """
        # Generate a unique cache key for the repository's settings.
        cache_key = self.repo_setting_cache_key()

        # Attempt to retrieve the cached settings from.
        setting = await RepoSettingCache.get(cache_key)

        # If the cache is (-1) indicating an absence of setting:
        if setting == -1:
            return {}  # Return an empty dictionary, as no settings are available.

        # If error in setting (-2):
        elif setting == -2:
            # Retrieve the associated error message from the cache.
            error = await RepoSettingCache.get(cache_key + "_error")
            # Set the error context for further processing.
            set_context_values(setting_error=error)
            return {}  # Return an empty dictionary due to the error.

        # If settings are found in the cache:
        elif setting is not None:
            error = await RepoSettingCache.get(cache_key + "_error")
            if error:
                set_context_values(setting_error=error)
            return setting  # Return the cached settings.

        # If no relevant cache entry is found (cache miss):
        else:
            # Fetch repository settings from the database along with any errors encountered.
            setting, error = await self.fetch_repo_setting_from_db()

            # Determine the cache value based on the result.
            if error:
                # Case 1: An error occurred while fetching settings.
                # If no settings were fetched, mark the cache with -2 to indicate an error.
                # If settings were fetched but with an error, cache the settings and log the error.
                setting_cache = -2 if not setting else setting
                set_context_values(setting_error=error)  # Log the error in the context for debugging.
                await RepoSettingCache.set(cache_key + "_error", error)  # Cache the error details.
            elif not setting:
                # Case 2: No settings found in the database.
                setting_cache = -1  # Mark the cache to indicate no settings are available.
            else:
                # Case 3: Settings successfully retrieved without any errors.
                setting_cache = setting  # Cache the retrieved settings.

            # Cache the final resolved state (settings, no settings, or error marker).
            await RepoSettingCache.set(cache_key, setting_cache)
            return setting  # Return the retrieved settings (or an empty dictionary if absent).

    def remove_repo_specific_setting(self, setting):
        if setting:
            for key in self.repo_specific_keys:
                if setting.get(key):
                    for nested_key in setting[key]:
                        setting[key][nested_key] = None
        return setting

    async def team_level_settings(self):
        configuration = {}
        if self.team_id:
            configuration = await Configurations.get_or_none(
                configurable_id=self.team_id, configurable_type=SettingLevel.TEAM.value
            )
            return configuration.configuration if configuration else {}
        return configuration

    @classmethod
    def dd_level_settings(cls):
        return cls.DD_LEVEL_SETTINGS

    @classmethod
    def merge_setting(cls, base_config, override_config):
        """
        Merges an override configuration into a base configuration with specific rules for hierarchical inheritance
        and `is_override` constraints. This function is typically used to combine configurations from
        multiple levels, such as organization or repository levels, into a final configuration.

        Rules:
        - If a key exists in the `base_config` but not in `override_config`, the base value remains unchanged.
        - If a value in `base_config` is a dictionary, the function recursively merges the nested dictionary from `override_config`.
        - For the `enable` field:
            - Allow override if `is_override` not set in base config or `is_override` is True
            - If `is_override` is `False`, the `enable` field cannot be overridden by `override_config`.
        - For all other fields (non-dict fields), values from `override_config` take precedence.
        - For the key `[code_review_agent][agents]`:
            - If a key exists in both base and override, the value from override takes precedence.
            - If a key does not exist in base, it is added from override.
        """
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
        """
        Merge the `agents` key from `code_review_agent`, ensuring custom rules are applied.
        """
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

    async def update_repo_setting(self):
        """
        For understanding of errors:
        -> there are two type of errors
            -> A error that makes the complete repo_level setting invalid (Invalid Toml, Type mismatch with DD setting)
                In this case, is_invalid_setting = True
            -> A error because of that we drop specific attributes (CustomPrompt length exceed), we still use repo level setting
                but drop custom_prompt for specific agents.
                In this case, is_invalid_setting = False
        """
        # Generate the cache key
        cache_key = self.repo_setting_cache_key()

        # Fetch repo-level settings
        repo_level_settings, error = await self.repo_service.get_settings(self.default_branch)

        # Check if settings are invalid
        is_invalid_setting = True if error else False  # if error exists that means TOML is invalid

        # Validate the fetched repository settings against the default settings.
        # This is required to check if there are mismatches or errors in the attributes.
        # If type mismatch we set is_invalid_setting = True
        team_settings = await self.team_level_settings()
        if repo_level_settings and not is_invalid_setting:
            error, is_invalid_setting = self.validate_repo_settings(repo_level_settings, team_settings)

        # Handle error and cache settings
        repo_level_settings = await self.handle_error_and_cache(
            error, is_invalid_setting, repo_level_settings, cache_key
        )

        # Fetch repo details
        repo = await self.repo_service.fetch_repo()

        # Create or update the setting in the DB
        await self.create_or_update_repo_setting(repo, repo_level_settings, error, team_settings)

    def validate_repo_settings(self, repo_settings, team_settings):
        if repo_settings:
            errors, is_invalid_setting = self.validate_settings(self.dd_level_settings(), repo_settings)
            errors.update(self.validate_repo_merged_setting(self.dd_level_settings(), team_settings, repo_settings))
        else:
            errors, is_invalid_setting = None, True  # In case of missing repo level settings
        return errors, is_invalid_setting

    @classmethod
    def validate_repo_merged_setting(cls, dd_setting, team_setting, repo_setting):
        settings = cls.merge_setting(dd_setting, team_setting)
        settings = cls.merge_setting(settings, repo_setting)
        return cls.validate_mandatory_keys(settings, repo_setting)

    @classmethod
    def validate_team_merged_setting(cls, dd_setting, team_setting):
        settings = cls.merge_setting(dd_setting, team_setting)
        return cls.validate_mandatory_keys(settings, team_setting)

    @classmethod
    def validate_mandatory_keys(cls, merged_setting, level_specific_setting):
        errors = cls.validate_agents_keys(cls.agents(merged_setting), level_specific_setting)
        return errors

    @staticmethod
    def validate_agents_keys(agents, level_specific_setting):
        errors = {}
        error = ""
        for agent_name, agent_data in agents.items():
            missing_keys = []
            for key in ["agent_id", "display_name", "weight", "objective"]:
                if not agent_data.get(key):
                    missing_keys.append(key)
            if missing_keys:
                level_specific_setting["code_review_agent"]["agents"].pop(agent_name)
                error += f"- {agent_name}: {str(missing_keys)}\n"
        if error:
            error_type = SettingErrorType.MISSING_KEY.value
            errors[error_type] = f"{SETTING_ERROR_MESSAGE[error_type]}{error}"
        return errors

    async def handle_error_and_cache(self, error, is_invalid_setting, repo_level_settings, cache_key):
        if not repo_level_settings and not error:
            repo_level_settings = -1
        elif error:
            if is_invalid_setting:
                repo_level_settings = -2
            await RepoSettingCache.set(cache_key + "_error", error)

        await RepoSettingCache.set(cache_key, repo_level_settings)
        return repo_level_settings

    async def normalize_invalid_setting_for_db(self, repo_level_settings):
        if repo_level_settings in [-1, -2]:
            repo_level_settings = None
        return repo_level_settings

    async def create_or_update_repo_setting(self, repo, repo_settings, error, team_settings):
        if repo:
            repo_settings = await self.normalize_invalid_setting_for_db(repo_settings)
            existing_setting = await self.fetch_setting(repo.id, SettingLevel.REPO.value)
            await self.update_repo_agents(repo.id, repo_settings, existing_setting, team_settings)
            await self.create_or_update_setting(
                configurable_id=repo.id,
                configurable_type=SettingLevel.REPO.value,
                error=error,
                setting=repo_settings,
                saved_setting=existing_setting,
            )

    @classmethod
    async def fetch_setting(cls, configurable_id, configurable_type):
        # Fetch the existing setting for the given configurable ID and type.
        setting = await Configurations.get_or_none(configurable_id=configurable_id, configurable_type=configurable_type)
        return setting

    async def update_repo_agents(self, repo_id, repo_settings, repo_existing_settings, team_settings):
        if not repo_settings:
            return
        repo_existing_settings = repo_existing_settings.configuration if repo_existing_settings else {}
        dd_agents = self.agents(self.DD_LEVEL_SETTINGS)
        team_agents = self.agents(team_settings)
        repo_agents = self.agents(repo_settings)
        repo_existing_agents = self.agents(repo_existing_settings)
        updated_agent_ids, deleted_agent_ids = self.updated_and_deleted_agent_ids(repo_existing_agents, repo_agents)
        if updated_agent_ids or deleted_agent_ids:
            agents_data = self.agents_analytics_info(dd_agents, team_agents, repo_agents)
            agents_ids_to_update = updated_agent_ids + deleted_agent_ids
            updated_agents = self.create_agents_objects(repo_id, agents_ids_to_update, agents_data)
            await self.upsert_agents(updated_agents)

    @classmethod
    async def update_team_agents(cls, team_id, updated_team_setting, existing_team_setting):
        if not updated_team_setting:
            return
        existing_team_setting = existing_team_setting.configuration if existing_team_setting else {}
        team_agents = cls.agents(updated_team_setting)
        existing_team_agents = cls.agents(existing_team_setting)
        updated_agent_ids, deleted_agent_ids = cls.updated_and_deleted_agent_ids(team_agents, existing_team_agents)
        if updated_agent_ids or deleted_agent_ids:
            repo_ids = await Repos.filter(team_id=team_id).values_list("id", flat=True)
            repo_settings = await cls.repo_settings_by_ids(repo_ids)
            agents_ids_to_update = updated_agent_ids + deleted_agent_ids
            dd_agents = cls.agents(cls.DD_LEVEL_SETTINGS)

            updated_agents = []
            for repo_id in repo_ids:
                repo_setting = repo_settings.get(repo_id) or {}
                repo_agents = cls.agents(repo_setting)
                agents_data = cls.agents_analytics_info(dd_agents, team_agents, repo_agents)
                updated_agents.extend(cls.create_agents_objects(repo_id, agents_ids_to_update, agents_data))
            await cls.upsert_agents(updated_agents)

    @classmethod
    async def repo_settings_by_ids(cls, repo_ids):
        repo_settings = await Configurations.filter(
            configurable_id__in=repo_ids, configurable_type=SettingLevel.REPO.value
        )
        settings_by_ids = {setting.configurable_id: setting.configuration for setting in repo_settings}
        return settings_by_ids

    @classmethod
    def create_agents_objects(cls, repo_id, agent_ids, agents_data):
        agent_objects = []
        for agent_id in agent_ids:
            if agent_id in agents_data:
                agent = {"repo_id": repo_id, "agent_id": agent_id, **agents_data[agent_id]}
                agent_objects.append(Agents(**agent))
        return agent_objects

    @classmethod
    def agents(cls, setting):
        if setting:
            return setting.get("code_review_agent", {}).get("agents") or {}
        return {}

    @staticmethod
    async def upsert_agents(agents):
        if agents:
            await Agents.bulk_create(
                agents,
                batch_size=100,
                on_conflict=["agent_id", "repo_id"],
                update_fields=["display_name", "agent_name", "updated_at"],
            )

    @classmethod
    def updated_and_deleted_agent_ids(cls, existing_agents, updated_agents):
        existing_agents = cls.agent_data_by_id(existing_agents)
        updated_agents = cls.agent_data_by_id(updated_agents)
        updated_agent_ids, deleted_agent_ids = [], []
        for agent_id, agent in updated_agents.items():
            # agent_id not in existing_agents -> new agent added
            # agent != existing_agents[agent_id] -> agent updated
            if agent_id not in existing_agents or agent != existing_agents[agent_id]:
                updated_agent_ids.append(agent_id)
        deleted_agent_ids = [aid for aid in existing_agents if aid not in updated_agents]
        return updated_agent_ids, deleted_agent_ids

    @staticmethod
    def agent_data_by_id(agents):
        agents_by_id = {
            data["agent_id"]: {"agent_name": agent_name, "display_name": data.get("display_name", "")}
            for agent_name, data in agents.items()
        }
        return agents_by_id

    @classmethod
    def agents_analytics_info(cls, dd_agents, team_agents, repo_agents):
        return cls.agents_analytics_info_recursive([dd_agents, team_agents, repo_agents])

    @classmethod
    def agents_analytics_info_recursive(cls, level_agents_list, combined_agents=None):
        """Recursively fetch and combine agents info from all levels."""
        if combined_agents is None:
            combined_agents = {}

        if not level_agents_list:
            return combined_agents

        current_level_agents = level_agents_list[0]

        if current_level_agents:
            for agent_name, agent_info in current_level_agents.items():
                agent_id = agent_info["agent_id"]
                if agent_id in combined_agents:
                    # Update with lower-level agent name and display name
                    combined_agents[agent_id]["agent_name"] = agent_name
                    combined_agents[agent_id]["display_name"] = agent_info.get("display_name") or combined_agents[
                        agent_id
                    ].get("display_name", "")
                    combined_agents[agent_id]["severity"] = agent_info.get("severity") or combined_agents[agent_id].get(
                        "severity", ""
                    )
                else:
                    # Add new agent entry
                    combined_agents[agent_id] = {
                        "agent_name": agent_name,
                        "display_name": agent_info.get("display_name") or "",
                        "severity": agent_info.get("severity"),
                    }

        # Recursively process the remaining levels
        return cls.agents_analytics_info_recursive(level_agents_list[1:], combined_agents)

    def repo_setting_cache_key(self):
        scm_workspace_id = self.repo_service.workspace_id
        scm_repo_id = self.repo_service.repo_id
        scm = self.repo_service.vcs_type
        return f"{scm}_{scm_workspace_id}_{scm_repo_id}"

    async def fetch_repo_setting_from_db(self):
        repo = await self.repo_service.fetch_repo()
        if not repo:
            return {}, ""
        setting = await Configurations.get_or_none(configurable_id=repo.id, configurable_type=SettingLevel.REPO.value)
        if setting:
            if setting.configuration:
                return setting.configuration, setting.error or {}
            else:
                return {}, setting.error or {}
        return {}, {}

    @classmethod
    async def create_or_update_team_settings(cls, payload, query_params):
        """
        While passing payload as json, don't send null in any key instead send ""
        """
        try:
            payload = update_payload_with_jwt_data(query_params, payload)
            if isinstance(payload["setting"], dict):
                toml_settings = toml.dumps(payload["setting"])
                setting = toml.loads(toml_settings)
            else:
                setting = toml.loads(payload["setting"])
            workspace = await get_workspace(scm=payload["vcs_type"], scm_workspace_id=payload["scm_workspace_id"])
            errors = cls.validate_team_settings(cls.dd_level_settings(), setting)
            if errors:
                raise BadRequestException(f"Invalid Setting: {errors}")
            existing_setting = await cls.fetch_setting(workspace.team_id, SettingLevel.TEAM.value)
            await cls.update_team_agents(workspace.team_id, setting, existing_setting)
            await cls.create_or_update_setting(
                workspace.team_id, SettingLevel.TEAM.value, errors, setting, existing_setting
            )
        except (toml.TomlDecodeError, TypeError) as e:
            raise BadRequestException(f"Invalid toml: {e}")

    @classmethod
    def validate_team_settings(cls, dd_setting, org_setting):
        errors, is_invalid_setting = cls.validate_settings(dd_setting, org_setting)
        errors.update(cls.validate_team_merged_setting(dd_setting, org_setting))
        return errors

    @classmethod
    async def create_or_update_setting(cls, configurable_id, configurable_type, error, setting, saved_setting):
        """
        Creates or updates a configuration setting based on the given parameters.
        Deletes the setting if no error or valid configuration is provided.
        """
        # Prepare the payload with the necessary data for the configuration.
        payload = {
            "configurable_id": configurable_id,
            "configurable_type": configurable_type,
            "configuration": setting,
            "error": error,
        }

        # If no saved setting exists:
        if not saved_setting:
            # Create a new setting only if there is an error or a valid configuration.
            if error or setting:
                setting = Configurations(**payload)  # Instantiate a new configuration object.
                await setting.save()  # Save the new configuration to the database.

        # If a saved setting already exists:
        else:
            # Update the setting if there is an error or a valid configuration.
            if error or setting:
                # Add the ID of the existing setting to the payload.
                payload["id"] = saved_setting.id
                setting = Configurations(**payload)  # Create an updated configuration object.
                # Save and update specific fields (`configuration` and `error`) in the database.
                await setting.save(update_fields=["configuration", "error"], force_update=True)
            else:
                # If neither error nor valid configuration exists, delete the saved setting.
                await saved_setting.delete()

    @classmethod
    def fetch_setting_errors(cls, error_types):
        # Retrieve the current context's setting errors (if any).
        errors = get_context_value("setting_error")
        error_message = ""

        # Check if errors exist and if any of the specified error types are present in the errors.
        if errors and any(error_type in errors for error_type in error_types):
            # Iterate through the provided error types.
            for error_type in error_types:
                # If the current error type exists in the errors dictionary, append its message to error_message.
                if errors.get(error_type):
                    error_message += errors[error_type] + "\n\n"

        # Return the concatenated error messages.
        return error_message

    @classmethod
    def get_uuid_wise_agents(cls):
        setting = get_context_value("setting")
        agent_setting = setting["code_review_agent"]["agents"]
        pr_summary_setting = setting["pr_summary"]
        agents = {}
        for agent_name, agent_data in agent_setting.items():
            agent_data = {"agent_name": agent_name, **agent_data}
            agents[str(agent_data["agent_id"])] = agent_data
        agents[cls.summary_agent_id()] = {"agent_name": "pr_summary", **pr_summary_setting}
        return agents

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
    def get_agent_inclusion_exclusions(cls, agent_id=None):
        setting = get_context_value("setting")
        if agent_id == cls.summary_agent_id():
            # TODO: check this again when pr_summary inclusion_exclusion discussed
            inclusions = setting["pr_summary"].get("inclusions") or []
            exclusions = setting["pr_summary"].get("exclusions") or []
            return inclusions, exclusions
        else:
            global_exclusions = setting["code_review_agent"]["exclusions"] or []
            global_inclusions = setting["code_review_agent"]["inclusions"] or []
            agents = cls.get_uuid_wise_agents()
            if agent_id:
                inclusions = set(global_inclusions) | set(agents[agent_id].get("inclusions", []))
                exclusions = set(global_exclusions) | set(agents[agent_id].get("exclusions", []))
                return list(inclusions), list(exclusions)
            else:
                return list(global_inclusions), list(global_exclusions)

    @classmethod
    def agent_id_by_custom_name(cls, agent_name):
        agent_settings = cls.agents_settings()
        return agent_settings[agent_name]["agent_id"]

    @classmethod
    def predefined_name_to_custom_name(cls, agent_name):
        pre_defined_agents = cls.pre_defined_agents()
        if agent_name in pre_defined_agents:
            agent_id = pre_defined_agents[agent_name]["agent_id"]
            uuid_wise_agents = cls.get_uuid_wise_agents()
            return uuid_wise_agents[agent_id]["agent_name"]
        else:
            return agent_name

    @classmethod
    def custom_name_to_predefined_name(cls, agent_name):
        # In case of custom agent predefined_name will be same as custom agent
        all_agents = cls.agents_settings()
        if all_agents[agent_name]["is_custom_agent"]:
            return agent_name
        else:
            return cls.PREDEFINED_AGENTS_IDS_AND_NAMES[all_agents[agent_name]["agent_id"]]

    @classmethod
    def predefined_name_by_id(cls, agent_id):
        return cls.PREDEFINED_AGENTS_IDS_AND_NAMES.get(agent_id)

    @classmethod
    def custom_name_by_id(cls, agent_id):
        agents_settings = cls.get_uuid_wise_agents()
        return agents_settings[agent_id]["agent_name"]

    @classmethod
    def agent_setting_by_name(cls, agent_name):
        return cls.agents_settings().get(agent_name, {})
