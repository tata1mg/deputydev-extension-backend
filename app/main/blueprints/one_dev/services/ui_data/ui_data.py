from typing import Any, Dict, List

from app.backend_common.repository.extension_sessions.repository import (
    ExtensionSessionsRepository,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from deputydev_core.llm_handler.models.dto.message_thread_dto import MessageCallChainCategory


class UIProfile:
    @classmethod
    async def get_ui_profile(cls, user_team_id: int, session_type: str) -> Dict[str, Any]:
        try:
            sessions_ids = await ExtensionSessionsRepository.get_extension_sessions_ids(
                user_team_id=user_team_id, session_type=session_type
            )
            total_queries = await MessageThreadsRepository.get_total_user_queries(
                session_ids=sessions_ids, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
            )
            ui_profile_data = await cls.get_ui_profile_data(total_queries)
            return {"ui_profile_data": ui_profile_data}
        except Exception as e:  # noqa: BLE001
            raise BadRequestException(f"Failed to fetch ui profile data: {str(e)}")

    @classmethod
    async def get_ui_profile_data(cls, total_queries: int) -> List[Dict[str, Any]]:
        return [
            {
                "label": "Usage",
                "type": "Expand",
                "icon": "https://onemg.gumlet.io/dd_usage_24_03.png",
                "data": f"""<div className="p-2 bg-gray-500/20 rounded-bl rounded-br">
                    <p className="text-md">Current Plan - <b>Premium</b></p>
                    <div className="flex flex-col gap-2 mt-2">
                    <div className="w-full h-2 bg-green-500 rounded" />
                    <div className="flex justify-between">
                        <p className="text-md">Requests</p>
                        <div className="text-sm text-gray-400 text-right">{total_queries} of Unlimited</div>
                    </div>
                    </div>
                </div>""",
            },
            {
                "label": "Feature Request",
                "type": "Hyperlink",
                "icon": "https://onemg.gumlet.io/dd_request_feature_24_03.png",
                "url": "https://forms.gle/Abd1FJJVf3J2daLP7",
            },
            {
                "label": "Docs",
                "type": "Hyperlink",
                "icon": "https://onemg.gumlet.io/dd_docs_logo_26_03.png",
                "url": "https://onedoc.ekdosis.com/docs/deputydev/content/DeputyDev%20-%20VSCode%20plugin/",
            },
            {
                "label": "Report a Bug",
                "type": "Hyperlink",
                "icon": "https://onemg.gumlet.io/dd_report_bug_24_03.png",
                "url": "https://forms.gle/s2Youjzo63YU9k7s9",
            },
            {
                "label": "r/DeputyDev",
                "type": "Hyperlink",
                "icon": "https://onemg.gumlet.io/dd_reddit_logo_v2_23_03.png",
                "url": "https://www.reddit.com/r/DeputyDev/",
            },
        ]
