import copy
import toml
from app.backend_common.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.caches.repo_setting_cache import RepoSettingCache
from app.main.blueprints.deputy_dev.constants.constants import SettingLevel
from app.main.blueprints.deputy_dev.models.dao.postgres import Agents, Configurations, Repos
from app.main.blueprints.deputy_dev.utils import get_workspace, update_payload_with_jwt_data
from app.common.utils.context_vars import context_var, get_context_value, set_context_values
from app.main.blueprints.deputy_dev.services.setting.setting_validator import SettingValidator
from app.main.blueprints.deputy_dev.services.setting.setting_helper import SettingHelper
from torpedo.exceptions import BadRequestException


class SettingService:
    Helper = SettingHelper
    Validator = SettingValidator

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
        team_level_settings = self.Helper.remove_repo_specific_setting(team_level_settings)
        base_settings = self.Helper.dd_level_settings()
        final_setting = copy.deepcopy(base_settings)
        final_setting = self.Helper.merge_setting(final_setting, team_level_settings)
        final_setting = self.Helper.merge_setting(final_setting, repo_level_settings)
        set_context_values(setting=final_setting)
        return final_setting

    async def repo_level_settings(self):
        cache_key = self.repo_setting_cache_key()
        setting = await RepoSettingCache.get(cache_key)
        if setting == -1:
            return {}
        elif setting == -2:
            error = await RepoSettingCache.get(cache_key + "_error")
            set_context_values(setting_error=error)
            return {}
        elif setting is not None:
            error = await RepoSettingCache.get(cache_key + "_error")
            if error:
                set_context_values(setting_error=error)
            return setting
        else:
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

    async def team_level_settings(self):
        configuration = {}
        if self.team_id:
            configuration = await Configurations.get_or_none(
                configurable_id=self.team_id, configurable_type=SettingLevel.TEAM.value
            )
            return configuration.configuration if configuration else {}
        return configuration

    async def update_repo_setting(self):
        cache_key = self.repo_setting_cache_key()
        repo_level_settings, error = await self.repo_service.get_settings(self.default_branch)
        is_invalid_setting = True if error else False
        team_settings = await self.team_level_settings()
        if repo_level_settings and not is_invalid_setting:
            error, is_invalid_setting = self.Validator.validate_repo_settings(repo_level_settings, team_settings)
        repo_level_settings = await self.handle_error_and_cache(
            error, is_invalid_setting, repo_level_settings, cache_key
        )
        repo = await self.repo_service.fetch_repo()
        await self.create_or_update_repo_setting(repo, repo_level_settings, error, team_settings)

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
        setting = await Configurations.get_or_none(configurable_id=configurable_id, configurable_type=configurable_type)
        return setting

    async def update_repo_agents(self, repo_id, repo_settings, repo_existing_settings, team_settings):
        if not repo_settings:
            return
        repo_existing_settings = repo_existing_settings.configuration if repo_existing_settings else {}
        dd_agents = self.Helper.agents(self.Helper.DD_LEVEL_SETTINGS)
        team_agents = self.Helper.agents(team_settings)
        repo_agents = self.Helper.agents(repo_settings)
        repo_existing_agents = self.Helper.agents(repo_existing_settings)
        updated_agent_ids, deleted_agent_ids = self.updated_and_deleted_agent_ids(repo_existing_agents, repo_agents)
        if updated_agent_ids or deleted_agent_ids:
            agents_data = self.Helper.agents_analytics_info(dd_agents, team_agents, repo_agents)
            agents_ids_to_update = updated_agent_ids + deleted_agent_ids
            updated_agents = self.create_agents_objects(repo_id, agents_ids_to_update, agents_data)
            await self.upsert_agents(updated_agents)

    @classmethod
    def create_agents_objects(cls, repo_id, agent_ids, agents_data):
        agent_objects = []
        for agent_id in agent_ids:
            if agent_id in agents_data:
                agent = {"repo_id": repo_id, "agent_id": agent_id, **agents_data[agent_id]}
                agent_objects.append(Agents(**agent))
        return agent_objects

    @classmethod
    def updated_and_deleted_agent_ids(cls, existing_agents, updated_agents):
        existing_agents = cls.Helper.agent_data_by_id(existing_agents)
        updated_agents = cls.Helper.agent_data_by_id(updated_agents)
        updated_agent_ids, deleted_agent_ids = [], []
        for agent_id, agent in updated_agents.items():
            # agent_id not in existing_agents -> new agent added
            # agent != existing_agents[agent_id] -> agent updated
            if agent_id not in existing_agents or agent != existing_agents[agent_id]:
                updated_agent_ids.append(agent_id)
        deleted_agent_ids = [aid for aid in existing_agents if aid not in updated_agents]
        return updated_agent_ids, deleted_agent_ids

    @staticmethod
    async def upsert_agents(agents):
        if agents:
            await Agents.bulk_create(
                agents,
                batch_size=100,
                on_conflict=["agent_id", "repo_id"],
                update_fields=["display_name", "agent_name", "updated_at"],
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
    async def create_or_update_team_settings(cls, payload, query_params):
        try:
            payload = update_payload_with_jwt_data(query_params, payload)
            if isinstance(payload["setting"], dict):
                toml_settings = toml.dumps(payload["setting"])
                setting = toml.loads(toml_settings)
            else:
                setting = toml.loads(payload["setting"])
            workspace = await get_workspace(scm=payload["vcs_type"], scm_workspace_id=payload["scm_workspace_id"])
            errors = cls.Validator.validate_team_settings(cls.Helper.dd_level_settings(), setting)
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
    async def update_team_agents(cls, team_id, updated_team_setting, existing_team_setting):
        if not updated_team_setting:
            return
        existing_team_setting = existing_team_setting.configuration if existing_team_setting else {}
        team_agents = cls.Helper.agents(updated_team_setting)
        existing_team_agents = cls.Helper.agents(existing_team_setting)
        updated_agent_ids, deleted_agent_ids = cls.updated_and_deleted_agent_ids(team_agents, existing_team_agents)
        if updated_agent_ids or deleted_agent_ids:
            repo_ids = await Repos.filter(team_id=team_id).values_list("id", flat=True)
            repo_settings = await cls.repo_settings_by_ids(repo_ids)
            agents_ids_to_update = updated_agent_ids + deleted_agent_ids
            dd_agents = cls.Helper.agents(cls.Helper.DD_LEVEL_SETTINGS)

            updated_agents = []
            for repo_id in repo_ids:
                repo_setting = repo_settings.get(repo_id) or {}
                repo_agents = cls.Helper.agents(repo_setting)
                agents_data = cls.Helper.agents_analytics_info(dd_agents, team_agents, repo_agents)
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
    async def create_or_update_setting(cls, configurable_id, configurable_type, error, setting, saved_setting):
        payload = {
            "configurable_id": configurable_id,
            "configurable_type": configurable_type,
            "configuration": setting,
            "error": error,
        }

        if not saved_setting:
            if error or setting:
                setting = Configurations(**payload)
                await setting.save()
        else:
            if error or setting:
                payload["id"] = saved_setting.id
                setting = Configurations(**payload)
                await setting.save(update_fields=["configuration", "error"], force_update=True)
            else:
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
