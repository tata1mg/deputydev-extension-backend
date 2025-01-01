import copy
from pathlib import Path

import toml
from torpedo.exceptions import BadRequestException

from app.common.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.caches.repo_setting_cache import RepoSettingCache
from app.main.blueprints.deputy_dev.constants.constants import (
    CUSTOM_PROMPT_CHAR_LIMIT,
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
    SettingLevel,
)
from app.main.blueprints.deputy_dev.models.dao.postgres import Configurations
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    context_var,
    get_context_value,
    set_context_values,
)
from app.main.blueprints.deputy_dev.utils import (
    get_workspace,
    update_payload_with_jwt_data,
)


class SettingService:
    DD_LEVEL_SETTINGS = toml.load(Path("./settings.toml"))
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

    def merge_setting(self, base_config, override_config):
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
        """

        # Return the base config as-is if there's no override config
        if not override_config:
            return base_config

        # Iterate over each key-value pair in the base configuration
        for key, value in base_config.items():
            # Skip keys not in the override config or with None values in the override config
            if key not in override_config or override_config[key] is None:
                continue

            # If the base value is a dictionary, recursively merge dictionaries from both configs
            if isinstance(value, dict):
                base_config[key] = self.merge_setting(value, override_config[key])

            else:
                # Handle the 'enable' field based on `is_override` rules
                if key == "enable":
                    # Allow override if `is_override` not set in base config or `is_override` is True
                    if "is_override" not in base_config or base_config["is_override"]:
                        base_config[key] = override_config[key]
                elif key in ["exclusions", "inclusions"]:
                    # for ["exclusions", "inclusions"] union of complete hierarchy is required.
                    base_config[key] = list(set(base_config[key]) | set(override_config[key]))
                else:
                    # For non-'enable' fields, apply the override config value directly
                    base_config[key] = override_config[key]

        return base_config

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
        # Generate the cache key for storing repository settings.
        cache_key = self.repo_setting_cache_key()

        # Fetch the repository-level settings using the default branch.
        # If there is an error, it might indicate an invalid setting.
        repo_level_settings, error = await self.repo_service.get_settings(self.default_branch)
        is_invalid_setting = True if error else False  # if error exists that means TOML is invalid

        # Validate the fetched repository settings against the default settings.
        # This is required to check if there are mismatches or errors in the attributes.
        # If type mismatch we set is_invalid_setting = True
        if repo_level_settings and not is_invalid_setting:
            error, is_invalid_setting = self.validate_settings(self.dd_level_settings(), repo_level_settings)

        # Handle cases where no settings are found or there is an error.
        if not repo_level_settings and not error:
            # No settings available and no error: use a placeholder value (-1).
            repo_level_settings = -1
        elif error:
            # If there is an error, check if the entire setting is invalid.
            if is_invalid_setting:
                # Invalid setting error: use a placeholder value (-2).
                repo_level_settings = -2
            # Cache the error for further reference.
            await RepoSettingCache.set(cache_key + "_error", error)

        # Cache the current repository settings or the placeholder value.
        await RepoSettingCache.set(cache_key, repo_level_settings)

        # If the setting is completely invalid (-1 or -2), store None in the database.
        if repo_level_settings in [-1, -2]:  # Save in DB
            repo_level_settings = None

        # Fetch repository details to associate settings with a specific repository.
        repo = await self.repo_service.fetch_repo()
        if repo:
            # Create or update the settings in the database.
            await self.create_or_update_setting(
                configurable_id=repo.id,
                configurable_type=SettingLevel.REPO.value,
                error=error,
                setting=repo_level_settings,
            )

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
    async def create_or_update_org_settings(cls, payload, query_params):
        try:
            payload = update_payload_with_jwt_data(query_params, payload)
            setting = toml.loads(payload["setting"])
            workspace = await get_workspace(scm=payload["vcs_type"], scm_workspace_id=payload["scm_workspace_id"])
            error = cls.validate_settings(cls.dd_level_settings(), setting)
            if error:
                raise BadRequestException(f"Invalid toml: {error}")
            await cls.create_or_update_setting(workspace.team_id, SettingLevel.TEAM.value, error, setting)

        except toml.TomlDecodeError as e:
            raise BadRequestException(f"Invalid toml: {e}")

    @classmethod
    async def create_or_update_setting(cls, configurable_id, configurable_type, error, setting):
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

        # Fetch the existing setting for the given configurable ID and type.
        saved_setting = await Configurations.get_or_none(
            configurable_id=configurable_id, configurable_type=configurable_type
        )

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
