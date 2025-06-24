from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageCallChainCategory,
    MessageThreadActor,
    MessageThreadData,
    MessageType,
    TextBlockContent,
    TextBlockData,
    LLModels,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
import xxhash
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)
from app.main.blueprints.one_dev.models.dto.query_summaries import (
    QuerySummaryData,
)
from app.backend_common.caches.code_gen_tasks_cache import (
    CodeGenTasksCache,
)
from deputydev_core.utils.app_logger import AppLogger

class CancellationService:
    async def cancel(
           self,
           session_id:int
    ) -> None : 
        original_query, stored_llm_model, existing_query_id = await CodeGenTasksCache.get_session_data_for_db(session_id)

        if original_query:
            try:
                llm_model = LLModels(stored_llm_model)
                # Create the cancelled query message
                cancelled_query = f"[CANCELLED] {original_query}"

                # Check if query_id already exists in Redis
                if existing_query_id is None:
                    # Create new message thread only if query_id doesn't exist
                    data_hash = xxhash.xxh64(cancelled_query).hexdigest()
                    message_data = [
                        TextBlockData(
                            type=ContentBlockCategory.TEXT_BLOCK,
                            content=TextBlockContent(text=original_query),
                            content_vars={"query": original_query},
                        )
                    ]

                    message_thread = MessageThreadData(
                        session_id=session_id,
                        actor=MessageThreadActor.USER,
                        query_id=None,
                        message_type=MessageType.QUERY,
                        conversation_chain=[],
                        message_data=message_data,
                        data_hash=data_hash,
                        prompt_type="CODE_QUERY_SOLVER",
                        prompt_category="CODE_GENERATION",
                        llm_model=llm_model,
                        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
                    )

                    created_thread = await MessageThreadsRepository.create_message_thread(message_thread)
                    cancelled_query_id = created_thread.id
                else:
                    # Use existing query_id
                    cancelled_query_id = existing_query_id

                # Always create a summary during cancellation
                await QuerySummarysRepository.create_query_summary(
                    QuerySummaryData(
                        session_id=session_id,
                        query_id=cancelled_query_id,
                        summary=cancelled_query,
                    )
                )
            except Exception as ex:
                AppLogger.log_error(f"Error creating cancelled query entry: {ex}")
                return None
