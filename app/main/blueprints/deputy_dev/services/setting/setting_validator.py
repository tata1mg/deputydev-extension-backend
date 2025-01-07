from typing import Union

from app.common.constants.constants import (
    CUSTOM_PROMPT_CHAR_LIMIT,
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
)
from app.main.blueprints.deputy_dev.services.setting.setting_helper import SettingHelper


class SettingValidator:
    """
    A class responsible for validating various levels of settings, including team, repository,
    and agent-specific configurations.
    """

    HELPER = SettingHelper

    @classmethod
    def validate_settings(cls, base_settings: dict, override_settings: dict) -> tuple[dict, bool]:
        """
        Validates the override settings against the base settings.

        Parameters:
        - base_settings (dict): The base settings to validate against.
        - override_settings (dict): The override settings to be validated.

        Returns:
        - tuple[dict, bool]: A dictionary of validation errors and a boolean indicating if settings are invalid.
        """
        errors = {}
        error_message = cls.validate_types(base_settings, override_settings)
        if error_message:
            error_type = SettingErrorType.INVALID_SETTING.value
            errors[error_type] = f"{SETTING_ERROR_MESSAGE[error_type]}{error_message}"
            return errors, True
        errors.update(cls.validate_custom_prompts(override_settings))
        return errors, False

    @classmethod
    def validate_agents(cls, agents: dict) -> None:
        """
        Validates agent configurations and removes any agents without an 'agent_id'.

        Parameters:
        - agents (dict): A dictionary containing agent configurations.

        Returns:
        - None
        """
        for agent_name, agent_data in list(agents.items()):
            if "agent_id" not in agent_data:
                agents.pop(agent_name)

    @classmethod
    def validate_types(cls, base_settings: dict, override_settings: dict, key_path: str = "") -> str:
        """
        Validates types of settings recursively.

        Parameters:
        - base_settings (dict): The base settings with expected types.
        - override_settings (dict): The override settings to validate.
        - key_path (str): Current path of the key being validated (for error messages).

        Returns:
        - str: A string containing error messages for type mismatches.
        """
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
    def validate_custom_prompts(cls, setting: dict) -> dict:
        """
        Validates custom prompts in the settings.

        Parameters:
        - setting (dict): The settings containing custom prompts.

        Returns:
        - dict: A dictionary of validation errors for custom prompts.
        """
        errors = {}
        errors.update(cls._validate_agent_prompts(setting))
        errors.update(cls._validate_chat_prompt(setting))
        return errors

    @classmethod
    def _validate_agent_prompts(cls, setting: dict) -> dict:
        """
        Validates the custom prompts for agents.

        Parameters:
        - setting (dict): The settings containing agent-specific custom prompts.

        Returns:
        - dict: A dictionary of validation errors for agent prompts.
        """
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
            errors[error_type] = f"{SETTING_ERROR_MESSAGE[error_type]}{error}"
        return errors

    @classmethod
    def _validate_chat_prompt(cls, setting: dict) -> dict:
        """
        Validates the custom prompt for the chat setting.

        Parameters:
        - setting (dict): The settings containing the chat-specific custom prompt.

        Returns:
        - dict: A dictionary of validation errors for the chat prompt.
        """
        error, errors = "", {}
        chat_custom_prompt = setting.get("chat", {}).get("custom_prompt", "")
        if len(chat_custom_prompt) > CUSTOM_PROMPT_CHAR_LIMIT:
            error_type = SettingErrorType.INVALID_CHAT_SETTING.value
            error = f", provided prompt length is {len(chat_custom_prompt)}."
            setting["chat"]["custom_prompt"] = ""
            errors[error_type] = f"{SETTING_ERROR_MESSAGE[error_type]}{error}"
        return errors

    @classmethod
    def validate_repo_settings(cls, repo_settings: dict, team_settings: dict) -> tuple[Union[dict, None], bool]:
        """
        Validates repository settings and merges them with team settings.

        Parameters:
        - repo_settings (dict): The repository-specific settings.
        - team_settings (dict): The team-level settings.

        Returns:
        - tuple[dict | None, bool]: A dictionary of validation errors and a boolean indicating invalid settings.
        """
        if repo_settings:
            errors, is_invalid_setting = cls.validate_settings(cls.HELPER.dd_level_settings(), repo_settings)
            errors.update(
                cls.validate_repo_merged_setting(cls.HELPER.dd_level_settings(), team_settings, repo_settings)
            )
        else:
            errors, is_invalid_setting = None, True
        return errors, is_invalid_setting

    @classmethod
    def validate_repo_merged_setting(cls, dd_setting: dict, team_setting: dict, repo_setting: dict) -> dict:
        """
        Validates mandatory keys in merged repository settings.

        Parameters:
        - dd_setting (dict): The default DD-level settings.
        - team_setting (dict): The team-level settings.
        - repo_setting (dict): The repository-specific settings.

        Returns:
        - dict: A dictionary of validation errors for mandatory keys.
        """
        settings = cls.HELPER.merge_setting(dd_setting, team_setting)
        settings = cls.HELPER.merge_setting(settings, repo_setting)
        return cls.validate_mandatory_keys(settings, repo_setting)

    @classmethod
    def validate_mandatory_keys(cls, merged_setting: dict, level_specific_setting: dict) -> dict:
        """
        Validates mandatory keys in the merged settings.

        Parameters:
        - merged_setting (dict): The merged settings.
        - level_specific_setting (dict): The level-specific settings being validated.

        Returns:
        - dict: A dictionary of validation errors for missing keys.
        """
        errors = cls.validate_agents_keys(cls.HELPER.agents(merged_setting), level_specific_setting)
        return errors

    @staticmethod
    def validate_agents_keys(agents: dict, level_specific_setting: dict) -> dict:
        """
        Validates the keys for agents in the settings.

        Parameters:
        - agents (dict): The agent configurations.
        - level_specific_setting (dict): The level-specific settings containing the agents.

        Returns:
        - dict: A dictionary of validation errors for missing agent keys.
        """
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

    @classmethod
    def validate_team_settings(cls, dd_setting: dict, org_setting: dict) -> dict:
        """
        Validates team settings by merging them with DD-level settings.

        Parameters:
        - dd_setting (dict): The default DD-level settings.
        - org_setting (dict): The organization-level settings.

        Returns:
        - dict: A dictionary of validation errors for the team settings.
        """
        errors, is_invalid_setting = cls.validate_settings(dd_setting, org_setting)
        errors.update(cls.validate_team_merged_setting(dd_setting, org_setting))
        return errors

    @classmethod
    def validate_team_merged_setting(cls, dd_setting: dict, team_setting: dict) -> dict:
        """
        Validates mandatory keys in merged team settings.

        Parameters:
        - dd_setting (dict): The default DD-level settings.
        - team_setting (dict): The team-level settings.

        Returns:
        - dict: A dictionary of validation errors for missing keys in team settings.
        """
        settings = cls.HELPER.merge_setting(dd_setting, team_setting)
        return cls.validate_mandatory_keys(settings, team_setting)
