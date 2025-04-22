import asyncio
from deputydev_core.utils.app_logger import AppLogger
from typing import Dict, Any, Optional, List
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dao.postgres.saved_urls import SavedURL
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.urls.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.one_dev.services.urls.prompts.factory import PromptFeatureFactory
from app.backend_common.services.llm.dataclasses.main import NonStreamingParsedLLMCallResponse
from app.backend_common.models.dto.message_thread_dto import LLModels, MessageCallChainCategory


class UrlService:
    @staticmethod
    async def get_saved_urls(user_team_id: int, limit: int, offset: int, client_data: ClientData) -> Dict[str, Any]:
        # Fetch saved URLs
        urls = (
            await SavedURL.filter(user_team_id=user_team_id, is_deleted=False)
            .order_by("-created_at")
            .offset(offset)
            .limit(limit)
        )

        # Count total number of saved URLs
        total_count = await SavedURL.filter(user_team_id=user_team_id, is_deleted=False).count()

        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit
        page_number = offset // limit

        # Prepare the response
        url_list = [
            {
                "id": url.id,
                "url": url.url,
                "name": url.name,
                "last_indexed": url.last_indexed.isoformat() if url.last_indexed else None,
            }
            for url in urls
        ]

        return {
            "urls": url_list,
            "meta": {"page_number": page_number, "total_pages": total_pages, "total_count": total_count},
        }

    @classmethod
    async def summarize_urls_long_content(cls, session_id, content):
        llm_handler = LLMHandler(prompt_features=PromptFeatures, prompt_factory=PromptFeatureFactory)
        max_retries = 2
        response: Optional[NonStreamingParsedLLMCallResponse] = None
        for attempt in range(max_retries + 1):
            try:
                llm_response = await llm_handler.start_llm_query(
                    session_id=session_id,
                    prompt_feature=PromptFeatures.URL_SUMMARIZATION,
                    llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                    prompt_vars={"content": content},
                    call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
                )
                if llm_response:
                    if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                        raise ValueError("Expected NonStreamingParsedLLMCallResponse")
                    response = llm_response
                    break
            except Exception as e:
                AppLogger.log_warn(f"URL summarization call Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)  # Optional: add a delay

            if response:
                import pdb
                pdb.set_trace()
                # TODO: handling of response
                pass

            return []
