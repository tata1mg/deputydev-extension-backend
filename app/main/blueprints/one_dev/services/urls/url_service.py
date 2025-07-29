from typing import Any, Dict, Optional

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.url import UrlDto
from app.main.blueprints.one_dev.repository.url_repository import UrlRepository
from app.main.blueprints.one_dev.services.urls.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.urls.prompts.factory import (
    PromptFeatureFactory,
)
from deputydev_core.utils.app_logger import AppLogger


class UrlService:
    @classmethod
    async def get_saved_urls(cls, user_team_id: int, limit: int, offset: int) -> Dict[str, Any]:
        urls, total_count = await UrlRepository.list_urls_with_count(
            user_team_id=user_team_id, limit=limit, offset=offset
        )
        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit
        page_number = (offset // limit) + 1
        # Prepare the response
        url_list = [cls.parse_url(UrlDto(**url)) for url in urls]
        return {
            "urls": url_list,
            "meta": {"page_number": page_number, "total_pages": total_pages, "total_count": total_count},
        }

    @classmethod
    async def summarize_urls_long_content(cls, session_id, content):
        llm_handler = LLMHandler(prompt_features=PromptFeatures, prompt_factory=PromptFeatureFactory)
        response: Optional[NonStreamingParsedLLMCallResponse] = None
        try:
            llm_response = await llm_handler.start_llm_query(
                session_id=session_id,
                prompt_feature=PromptFeatures.URL_SUMMARIZATION,
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                prompt_vars={"content": content},
                call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
            )
            if llm_response:
                if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                    raise ValueError("Expected NonStreamingParsedLLMCallResponse")
                response = llm_response
        except Exception as e:
            AppLogger.log_warn(f"URL summarization call failed: {e}")

        if response:
            generated_explanation = response.parsed_content[0].get("explanation")
            return generated_explanation
        return ""

    @classmethod
    async def save_url(cls, payload: "UrlDto"):
        url = await UrlRepository.save_url(payload)
        return cls.parse_url(url)

    @classmethod
    async def update_url(cls, payload: "UrlDto"):
        url = await UrlRepository.update_url(payload)
        return cls.parse_url(url)

    @classmethod
    async def delete_url(cls, url_id):
        await UrlRepository.delete_url(url_id)

    @classmethod
    def parse_url(cls, url: "UrlDto"):
        keys = ["id", "name", "url", "last_indexed"]
        data = url.model_dump(include=set(keys))
        data["last_indexed"] = url.last_indexed.isoformat() if url.last_indexed else None
        return data
