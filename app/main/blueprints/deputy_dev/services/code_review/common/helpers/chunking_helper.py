from app.backend_common.constants.constants import MAX_RELEVANT_CHUNKS
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.utils import is_path_included


class ChunkingHelper:
    @classmethod
    def agent_wise_relevant_chunks(cls, ranked_snippets_list):
        agents = SettingService.helper.get_uuid_wise_agents()
        remaining_agents = len(agents)

        relevant_chunks = {agent_id: [] for agent_id in agents}

        for snippet in ranked_snippets_list:
            if remaining_agents == 0:
                break

            path = snippet.denotation

            for agent_id, agent_info in agents.items():
                # Skip if the agent already has the required number of chunks
                if len(relevant_chunks[agent_id]) >= MAX_RELEVANT_CHUNKS:
                    continue

                inclusions, exclusions = SettingService.helper.get_agent_inclusion_exclusions(agent_id)

                # Check if the path is relevant
                if is_path_included(path, exclusions, inclusions):
                    relevant_chunks[agent_id].append(snippet)

                    # Decrement the counter when the agent reaches the chunk limit
                    if len(relevant_chunks[agent_id]) == MAX_RELEVANT_CHUNKS:
                        remaining_agents -= 1

                        # Exit the loop early if all agents are fulfilled
                        if remaining_agents == 0:
                            break

        return relevant_chunks
