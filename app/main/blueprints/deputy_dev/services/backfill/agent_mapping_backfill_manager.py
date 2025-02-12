from app.backend_common.models.dao.postgres import Repos
from app.backend_common.services.pr.pr_factory import PRFactory
from app.backend_common.services.repo.repo_factory import RepoFactory
from app.common.utils.app_logger import AppLogger
from app.main.blueprints.deputy_dev.models.dao.postgres import PullRequests, PRComments, AgentCommentMappings
from app.main.blueprints.deputy_dev.services.comment.agent_comment_mapping_Service import AgentCommentMappingService
from app.main.blueprints.deputy_dev.utils import get_vcs_auth_handler, get_workspace
from app.main.blueprints.deputy_dev.services.setting.setting_service import SettingService
from app.backend_common.repository.db import DB
from typing import Dict, Any
from app.main.blueprints.deputy_dev.models.dao.postgres import Agents


class AgentMappingBackfillManager:
    @classmethod
    async def backfill_data(cls, payload):
        scm_workspace_id = payload["workspace_id"]
        vcs_type = payload["vcs_type"]
        pr_ids = payload["pr_ids"]
        auth_handler = await get_vcs_auth_handler(scm_workspace_id, vcs_type)
        workspace = await get_workspace(scm_workspace_id=scm_workspace_id, scm=vcs_type)
        pull_requests = await PullRequests.filter(id__in=pr_ids)
        pull_requests_by_repo_ids = {}
        for pull_request in pull_requests:
            if pull_request.repo_id not in pull_requests_by_repo_ids:
                pull_requests_by_repo_ids[pull_request.repo_id] = []
            pull_requests_by_repo_ids[pull_request.repo_id].append(pull_request)
        for repo_id, pull_requests in pull_requests_by_repo_ids.items():
            repo = await Repos.get(id=repo_id)
            repo_service = await RepoFactory.repo(
                vcs_type=vcs_type,
                repo_name=repo.name,
                workspace=workspace.name,
                workspace_slug=workspace.slug,
                workspace_id=scm_workspace_id,
                auth_handler=auth_handler,
            )
            settings = await SettingService(repo_service=repo_service, team_id=workspace.team_id).build()
            repo_agents_by_id = await cls.backfill_agents(repo_id)
            agent_id_by_display_names = cls.agent_id_by_display_names(repo_agents_by_id)
            display_names = list(agent_id_by_display_names.keys())
            for pull_request in pull_requests:
                agent_comment_mappings = []
                pr_service = await PRFactory.pr(
                    vcs_type=vcs_type,
                    repo_name=repo.name,
                    workspace=workspace.name,
                    workspace_id=workspace.scm_workspace_id,
                    workspace_slug=workspace.slug,
                    auth_handler=auth_handler,
                    pr_id=pull_request.scm_pr_id,
                    repo_service=repo_service,
                    fetch_pr_details=False,
                )
                saved_comments = await PRComments.filter(pr_id=pull_request.id)
                pr_comments = await pr_service.get_pr_comments()
                saved_comments_by_comment_id = {comment.scm_comment_id: comment for comment in saved_comments}
                pr_comments_by_comment_id = {str(comment.scm_comment_id): comment for comment in pr_comments}
                for comment_id, comment_obj in saved_comments_by_comment_id.items():
                    if comment_id in pr_comments_by_comment_id:
                        comment_body = pr_comments_by_comment_id[comment_id].body
                        for name in display_names:
                            if f"**{name.upper()}**" in comment_body.upper():
                                agent_comment_mappings.append(
                                    AgentCommentMappings(
                                        pr_comment_id=comment_obj.id,
                                        agent_id=agent_id_by_display_names[name]["id"],
                                        weight=agent_id_by_display_names[name]["weight"],
                                    )
                                )
                if agent_comment_mappings:
                    await AgentCommentMappingService.bulk_insert(agent_comment_mappings)
                AppLogger.log_info(f"Processing done for pr_id: {pull_request.id} repo_id: {pull_request.repo_id}")

    @classmethod
    async def backfill_agents(cls, repo_id):
        current_agents_by_id = SettingService.Helper.agents_setting_by_agent_uuid()
        agent_ids = list(current_agents_by_id.keys())
        agent_filter = {"repo_id": repo_id, "agent_id__in": agent_ids}
        saved_agents_by_id = await cls.fetch_agents(agent_filter)
        await cls.upsert_agents(repo_id, saved_agents_by_id, current_agents_by_id)
        saved_agents_by_id = await cls.fetch_agents(agent_filter)
        return saved_agents_by_id

    @staticmethod
    async def fetch_agents(agent_filter: Dict[str, Any]) -> Dict[str, Any]:
        agents = await DB.get_by_filters(
            Agents,
            filters=agent_filter,
        )
        agents_by_id = {str(agent.agent_id): agent for agent in agents}
        return agents_by_id

    @staticmethod
    async def upsert_agents(repo_id: str, saved_agents: Dict[str, Any], current_agents: Dict[str, dict]):
        new_agents = []
        is_new_agent_created = False
        for agent_id, agent_data in current_agents.items():
            if agent_id not in saved_agents:
                is_new_agent_created = True
                new_agents.append(
                    Agents(
                        agent_id=agent_id,
                        repo_id=repo_id,
                        display_name=agent_data["display_name"],
                        agent_name=agent_data["agent_name"],
                    )
                )
        await SettingService.upsert_agents(new_agents)
        return is_new_agent_created

    @classmethod
    def agent_id_by_display_names(cls, saved_agents_by_id):
        current_agents_by_id = SettingService.Helper.agents_setting_by_agent_uuid()
        agent_id_by_display_names = {}
        for agent_id, agent_obj in saved_agents_by_id.items():
            display_name = current_agents_by_id[agent_id]["display_name"]
            weight = current_agents_by_id[agent_id]["weight"]
            agent_id_by_display_names[display_name] = {"id": agent_obj.id, "weight": weight}
        return agent_id_by_display_names
