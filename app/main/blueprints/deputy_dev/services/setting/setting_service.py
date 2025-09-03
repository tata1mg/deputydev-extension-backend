import copy
from typing import Any, Dict, List, Optional, Tuple, Union

import toml
from deputydev_core.utils.context_vars import (
    context_var,
    get_context_value,
    set_context_values,
)

from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.main.blueprints.deputy_dev.caches.repo_setting_cache import RepoSettingCache
from app.main.blueprints.deputy_dev.constants.constants import SettingLevel
from app.main.blueprints.deputy_dev.models.dao.postgres import (
    Agents,
    Configurations,
    Repos,
)
from app.main.blueprints.deputy_dev.services.setting.setting_helper import SettingHelper
from app.main.blueprints.deputy_dev.services.setting.setting_validator import (
    SettingValidator,
)
from app.main.blueprints.deputy_dev.utils import (
    get_workspace,
    update_payload_with_jwt_data,
)


class SettingService:
    helper = SettingHelper
    validator = SettingValidator

    def __init__(
        self, repo_service: BaseRepo, team_id: Optional[int] = None, default_branch: Optional[str] = None
    ) -> None:
        """
        Initialize the SettingService.

        Args:
            repo_service (BaseRepo): The repository service to interact with repositories.
            team_id (Optional[int]): The ID of the team. Defaults to None.
            default_branch (Optional[str]): The default branch of the repository. Defaults to None.
        """
        self.repo_service = repo_service
        self.team_id = team_id
        self.default_branch = default_branch

    async def build(self) -> Dict[str, Any]:
        """
        Build and return the final settings by merging default, team-level, and repo-level settings.

        Returns:
            Dict[str, Any]: The merged final settings.
        """
        if "setting" in context_var.get():
            # Retrieve setting from context if already set.
            setting = get_context_value("setting")
            return setting

        # Get default branch for the repository.
        self.default_branch = await self.repo_service.get_default_branch()

        # Fetch repository-level and team-level settings.
        repo_level_settings = await self.repo_level_settings()
        team_level_settings = await self.team_level_settings()

        # Remove repository-specific settings from team-level settings.
        team_level_settings = self.helper.remove_repo_specific_setting(team_level_settings)

        # Retrieve base (default) settings.
        base_settings = self.helper.dd_level_settings()
        final_setting = copy.deepcopy(base_settings)

        # Merge settings in the order: base -> team -> repository.
        final_setting = self.helper.merge_setting(final_setting, team_level_settings)
        final_setting = self.helper.merge_setting(final_setting, repo_level_settings)

        # Cache the final settings in context.
        set_context_values(setting=final_setting)
        return final_setting

    async def repo_level_settings(self) -> Dict[str, Any]:
        """
        Fetch repository-level settings either from cache or database.

        Returns:
            Dict[str, Any]: The repository-level settings.
        """
        cache_key = self.repo_setting_cache_key()
        setting = await RepoSettingCache.get(cache_key)

        if setting == -1:
            # Cache indicates no settings exist.
            return {}
        elif setting == -2:
            # Cache indicates invalid settings with an associated error.
            error = await RepoSettingCache.get(cache_key + "_error")
            set_context_values(setting_error=error)
            return {}
        elif setting is not None:
            # Return cached settings if available.
            error = await RepoSettingCache.get(cache_key + "_error")
            if error:
                set_context_values(setting_error=error)
            return setting
        else:
            # Fetch settings from the database if not cached.
            setting, error = await self.fetch_repo_setting_from_db()
            if error:
                setting_cache = -2 if not setting else setting
                set_context_values(setting_error=error)
                await RepoSettingCache.set(cache_key + "_error", error)
            elif not setting:
                setting_cache = -1
            else:
                setting_cache = setting

            await RepoSettingCache.set(cache_key, setting_cache)
            return setting

    async def team_level_settings(self) -> Dict[str, Any]:
        """
        Fetch team-level settings from the database.

        Returns:
            Dict[str, Any]: The team-level settings.
        """
        configuration = {}
        if self.team_id:
            configuration = await Configurations.get_or_none(
                configurable_id=self.team_id, configurable_type=SettingLevel.TEAM.value
            )
            return configuration.configuration if configuration else {}
        return configuration

    async def update_repo_setting(self) -> None:
        """
        Update repository settings and cache them.

        Returns:
            None
        """
        cache_key = self.repo_setting_cache_key()
        repo_level_settings, error = await self.repo_service.get_settings(self.default_branch)
        is_invalid_setting = True if error else False

        # Fetch team settings for validation.
        team_settings = await self.team_level_settings()

        if repo_level_settings and not is_invalid_setting:
            error, is_invalid_setting = self.validator.validate_repo_settings(repo_level_settings, team_settings)

        # Handle errors and cache the repository settings.
        repo_level_settings = await self.handle_error_and_cache(
            error, is_invalid_setting, repo_level_settings, cache_key
        )

        # Fetch repository data and create or update settings in the database.
        repo = await self.repo_service.fetch_repo()
        await self.create_or_update_repo_setting(repo, repo_level_settings, error, team_settings)

    async def handle_error_and_cache(
        self, error: Optional[str], is_invalid_setting: bool, repo_level_settings: Dict[str, Any], cache_key: str
    ) -> Dict[str, Any]:
        """
        Handle errors and cache the repository settings.

        Args:
            error (Optional[str]): The error message, if any.
            is_invalid_setting (bool): Whether the settings are invalid.
            repo_level_settings (Dict[str, Any]): The repository-level settings.
            cache_key (str): The cache key.

        Returns:
            Dict[str, Any]: The processed repository settings.
        """
        if not repo_level_settings and not error:
            repo_level_settings = -1
        elif error:
            if is_invalid_setting:
                repo_level_settings = -2
            await RepoSettingCache.set(cache_key + "_error", error)

        await RepoSettingCache.set(cache_key, repo_level_settings)
        return repo_level_settings

    @classmethod
    async def normalize_invalid_setting_for_db(
        cls, repo_level_settings: Union[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize invalid settings for database storage.

        Args:
            repo_level_settings (Union[Dict[str, Any], int]): The repository-level settings.

        Returns:
            Optional[Dict[str, Any]]: The normalized settings.
        """
        if repo_level_settings in [-1, -2]:
            repo_level_settings = None
        return repo_level_settings

    async def create_or_update_repo_setting(
        self,
        repo: Optional[Any],
        repo_settings: Optional[Dict[str, Any]],
        error: Optional[str],
        team_settings: Dict[str, Any],
    ) -> None:
        """
        Create or update repository settings in the database.

        Args:
            repo (Optional[Any]): The repository object.
            repo_settings (Optional[Dict[str, Any]]): The repository-level settings.
            error (Optional[str]): The error message, if any.
            team_settings (Dict[str, Any]): The team-level settings.

        Returns:
            None
        """
        if repo:
            repo_settings = await self.normalize_invalid_setting_for_db(repo_settings)
            existing_setting = await self.fetch_setting(repo.id, SettingLevel.REPO.value)

            # Update agents and create/update settings in the database.
            await self.update_repo_agents(repo.id, repo_settings, existing_setting, team_settings)
            await self.create_or_update_setting(
                configurable_id=repo.id,
                configurable_type=SettingLevel.REPO.value,
                error=error,
                setting=repo_settings,
                saved_setting=existing_setting,
            )

    @classmethod
    async def fetch_setting(cls, configurable_id: int, configurable_type: str) -> Optional[Any]:
        """
        Fetch a specific setting from the database.

        Args:
            configurable_id (int): The ID of the configurable entity.
            configurable_type (str): The type of the configurable entity.

        Returns:
            Optional[Any]: The fetched setting object.
        """
        return await Configurations.get_or_none(configurable_id=configurable_id, configurable_type=configurable_type)

    async def update_repo_agents(
        self,
        repo_id: int,
        repo_settings: Optional[Dict[str, Any]],
        repo_existing_settings: Optional[Any],
        team_settings: Dict[str, Any],
    ) -> None:
        """
        Update agents for a specific repository.

        Args:
            repo_id (int): The ID of the repository.
            repo_settings (Optional[Dict[str, Any]]): The repository-level settings.
            repo_existing_settings (Optional[Any]): The existing repository-level settings.
            team_settings (Dict[str, Any]): The team-level settings.

        Returns:
            None
        """
        if not repo_settings:
            return

        repo_existing_settings = repo_existing_settings.configuration if repo_existing_settings else {}
        dd_agents = self.helper.agents(self.helper.DD_LEVEL_SETTINGS)
        team_agents = self.helper.agents(team_settings)
        repo_agents = self.helper.agents(repo_settings)
        repo_existing_agents = self.helper.agents(repo_existing_settings)

        # Determine updated and deleted agent IDs.
        updated_agent_ids, deleted_agent_ids = self.updated_and_deleted_agent_ids(repo_existing_agents, repo_agents)

        if updated_agent_ids or deleted_agent_ids:
            agents_data = self.helper.agents_analytics_info(dd_agents, team_agents, repo_agents)
            agents_ids_to_update = updated_agent_ids + deleted_agent_ids
            updated_agents = self.create_agents_objects(repo_id, agents_ids_to_update, agents_data)
            await self.upsert_agents(updated_agents)

    @classmethod
    def create_agents_objects(
        cls, repo_id: int, agent_ids: List[int], agents_data: Dict[int, Dict[str, Any]]
    ) -> List[Agents]:
        """
        Create agent objects for database insertion.

        Args:
            repo_id (int): The ID of the repository.
            agent_ids (List[int]): The list of agent IDs to be updated.
            agents_data (Dict[int, Dict[str, Any]]): Data associated with the agents.

        Returns:
            List[Agents]: The list of agent objects.
        """
        agent_objects = []
        for agent_id in agent_ids:
            if agent_id in agents_data:
                agent = {"repo_id": repo_id, "agent_id": agent_id, **agents_data[agent_id]}
                agent_objects.append(Agents(**agent))
        return agent_objects

    @classmethod
    def updated_and_deleted_agent_ids(
        cls, existing_agents: List[Dict[str, Any]], updated_agents: List[Dict[str, Any]]
    ) -> Tuple[List[int], List[int]]:
        """
        Identify updated and deleted agent IDs.

        Args:
            existing_agents (List[Dict[str, Any]]): Existing agents in the repository.
            updated_agents (List[Dict[str, Any]]): Updated agents for the repository.

        Returns:
            Tuple[List[int], List[int]]: A tuple containing updated and deleted agent IDs.
        """
        existing_agents = cls.helper.agent_data_by_id(existing_agents)
        updated_agents = cls.helper.agent_data_by_id(updated_agents)

        updated_agent_ids, deleted_agent_ids = [], []
        for agent_id, agent in updated_agents.items():
            if agent_id not in existing_agents or agent != existing_agents[agent_id]:
                updated_agent_ids.append(agent_id)

        deleted_agent_ids = [aid for aid in existing_agents if aid not in updated_agents]
        return updated_agent_ids, deleted_agent_ids

    @staticmethod
    async def upsert_agents(agents: List[Agents]) -> None:
        """
        Insert or update agents in the database.

        Args:
            agents (List[Agents]): The list of agent objects to be upserted.

        Returns:
            None
        """
        if agents:
            await Agents.bulk_create(
                agents,
                batch_size=100,
                on_conflict=["agent_id", "repo_id"],
                update_fields=["display_name", "agent_name", "updated_at"],
            )

    def repo_setting_cache_key(self) -> str:
        """
        Generate a cache key for repository settings.

        Returns:
            str: The cache key.
        """
        scm_workspace_id = self.repo_service.workspace_id
        scm_repo_id = self.repo_service.repo_id
        scm = self.repo_service.vcs_type
        return f"{scm}_{scm_workspace_id}_{scm_repo_id}"

    async def fetch_repo_setting_from_db(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Fetch repository settings from the database.

        Returns:
            Tuple[Dict[str, Any], Optional[str]]: A tuple containing the settings and error message, if any.
        """
        repo = await self.repo_service.fetch_repo()
        if not repo:
            return {}, ""

        setting = await Configurations.get_or_none(configurable_id=repo.id, configurable_type=SettingLevel.REPO.value)
        if setting:
            if setting.configuration:
                return setting.configuration, setting.error or {}
            else:
                return {}, setting.error or {}

        return {}, ""

    @classmethod
    async def create_or_update_team_settings(cls, payload: Dict[str, Any], query_params: Dict[str, Any]) -> None:
        """
        Creates or updates team-level settings based on the provided payload and query parameters.

        Parameters:
        - payload (dict): The payload containing the settings data and necessary identifiers.
            Example keys:
                - "setting": The settings configuration in TOML format or as a dictionary.
                - "vcs_type": The version control system type.
                - "scm_workspace_id": The workspace ID for the version control system.
        - query_params (dict): The query parameters containing authentication and context information.

        Returns:
        - None

        Raises:
        - BadRequestException: If the provided payload is invalid or if the settings validation fails.

        Description:
        This function validates the team settings provided in the payload. It fetches the existing team settings from the database,
        identifies changes to agents, and updates the settings and associated agents in the database.
        If any validation errors occur, they are raised as exceptions.
        """
        try:
            # Update the payload with JWT data from query parameters.
            payload = update_payload_with_jwt_data(query_params, payload)

            # Parse and validate the settings from the payload.
            if isinstance(payload["setting"], dict):
                toml_settings = toml.dumps(payload["setting"])
                setting = toml.loads(toml_settings)
            else:
                setting = toml.loads(payload["setting"])

            # Fetch the workspace information using VCS type and workspace ID.
            workspace = await get_workspace(scm=payload["vcs_type"], scm_workspace_id=payload["scm_workspace_id"])

            # Validate the team settings using the defined helper and validator.
            errors = cls.validator.validate_team_settings(cls.helper.dd_level_settings(), setting)
            if errors:
                raise BadRequestException(f"Invalid Setting: {errors}")

            # Fetch the existing team settings from the database.
            existing_setting = await cls.fetch_setting(workspace.team_id, SettingLevel.TEAM.value)

            # Update team agents based on the changes in the settings.
            await cls.update_team_agents(workspace.team_id, setting, existing_setting)

            # Create or update the team settings in the database.
            await cls.create_or_update_setting(
                workspace.team_id, SettingLevel.TEAM.value, errors, setting, existing_setting
            )

        except (toml.TomlDecodeError, TypeError) as e:
            # Raise an exception for invalid TOML or payload format.
            raise BadRequestException(f"Invalid toml: {e}")

    @classmethod
    async def update_team_agents(
        cls, team_id: int, updated_team_setting: Dict[str, Any], existing_team_setting: Union[Configurations, None]
    ) -> None:
        """
        Updates the team agents in the database based on the changes in the provided team settings.

        Parameters:
        - team_id (int): The ID of the team whose agents are being updated.
        - updated_team_setting (dict): The new team settings containing updated agent configurations.
        - existing_team_setting (Configurations | None): The current team settings retrieved from the database.

        Returns:
        - None

        Description:
        This function identifies updated and deleted agents by comparing the updated and existing settings.
        It retrieves repository IDs associated with the team, fetches their settings, and determines which
        agents need to be updated. Finally, it upserts the updated agents into the database.
        """
        if not updated_team_setting:
            return

        # Extract the existing configuration or set to an empty dictionary if None
        existing_team_setting = existing_team_setting.configuration if existing_team_setting else {}

        # Extract agents from the updated and existing settings
        team_agents = cls.helper.agents(updated_team_setting)
        existing_team_agents = cls.helper.agents(existing_team_setting)

        # Identify updated and deleted agents
        updated_agent_ids, deleted_agent_ids = cls.updated_and_deleted_agent_ids(team_agents, existing_team_agents)

        if updated_agent_ids or deleted_agent_ids:
            # Fetch repository IDs associated with the team
            repo_ids = await Repos.filter(team_id=team_id).values_list("id", flat=True)

            # Fetch settings for the repositories
            repo_settings = await cls.repo_settings_by_ids(repo_ids)

            # Combine updated and deleted agent IDs
            agents_ids_to_update = updated_agent_ids + deleted_agent_ids

            # Extract DD-level agents
            dd_agents = cls.helper.agents(cls.helper.DD_LEVEL_SETTINGS)

            # Prepare the updated agents list
            updated_agents = []
            for repo_id in repo_ids:
                repo_setting = repo_settings.get(repo_id) or {}
                repo_agents = cls.helper.agents(repo_setting)
                agents_data = cls.helper.agents_analytics_info(dd_agents, team_agents, repo_agents)
                updated_agents.extend(cls.create_agents_objects(repo_id, agents_ids_to_update, agents_data))

            # Insert or update agents in the database
            await cls.upsert_agents(updated_agents)

    @classmethod
    async def repo_settings_by_ids(cls, repo_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Fetches repository settings for a list of repository IDs.

        Parameters:
        - repo_ids (list[int]): A list of repository IDs for which settings are to be retrieved.

        Returns:
        - dict[int, dict]: A dictionary mapping repository IDs to their corresponding settings.

        Description:
        This function queries the database for configurations associated with the provided repository IDs
        and returns them as a dictionary. If a repository has no settings, it will not appear in the result.
        """
        # Query database for repository configurations
        repo_settings = await Configurations.filter(
            configurable_id__in=repo_ids, configurable_type=SettingLevel.REPO.value
        )

        # Map repository IDs to their respective configurations
        settings_by_ids = {setting.configurable_id: setting.configuration for setting in repo_settings}
        return settings_by_ids

    @classmethod
    async def create_or_update_setting(
        cls,
        configurable_id: int,
        configurable_type: str,
        error: str,
        setting: Dict[str, Any],
        saved_setting: Configurations | None,
    ) -> None:
        """
        Creates or updates a configuration record in the database.

        Parameters:
        - configurable_id (int): The ID of the entity (team or repository) for which the setting applies.
        - configurable_type (str): The type of the entity (e.g., 'team', 'repo').
        - error (str): Any error associated with the setting validation or update.
        - setting (dict): The configuration data to be stored.
        - saved_setting (Configurations | None): The current setting stored in the database, if it exists.

        Returns:
        - None

        Description:
        This function either creates a new configuration record, updates an existing one, or deletes
        the current configuration if neither settings nor errors are provided.
        """
        # Prepare the payload for the configuration record
        payload = {
            "configurable_id": configurable_id,
            "configurable_type": configurable_type,
            "configuration": setting,
            "error": error,
        }

        if not saved_setting:
            # Create a new configuration record if no existing record is found
            if error or setting:
                setting = Configurations(**payload)
                await setting.save()
        else:
            if error or setting:
                # Update the existing configuration record
                payload["id"] = saved_setting.id
                setting = Configurations(**payload)
                await setting.save(update_fields=["configuration", "error"], force_update=True)
            else:
                # Delete the configuration record if both error and setting are empty
                await saved_setting.delete()

    @classmethod
    def fetch_setting_errors(cls, error_types: List[str]) -> str:
        """
        Retrieves error messages related to specific error types from the context.

        Parameters:
        - error_types (list[str]): A list of error types to retrieve from the context.

        Returns:
        - str: Concatenated error messages for the specified error types.

        Description:
        This function fetches error messages stored in the current context and filters them based on the
        provided error types. It concatenates and returns matching error messages.
        """
        # Retrieve the current context's setting errors (if any).
        errors = get_context_value("setting_error")
        error_message = ""

        if errors and any(error_type in errors for error_type in error_types):
            for error_type in error_types:
                if errors.get(error_type):
                    error_message += errors[error_type] + "\n\n"

        return error_message
