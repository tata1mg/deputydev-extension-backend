from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List, Optional, Union

from app.common.constants.constants import MAX_ITERATIVE_CHUNKS
from deputydev_core.services.chunking.chunking_manager import ChunkingManger
from deputydev_core.services.embedding.base_embedding_manager import BaseEmbeddingManager
from deputydev_core.services.embedding.base_embedding_manager import BaseEmbeddingManager
from deputydev_core.services.repo.local_repo.base_local_repo_service import BaseLocalRepo
from deputydev_core.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from deputydev_core.services.search.dataclasses.main import SearchTypes
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.clients.http.service_clients.one_dev_client import OneDevClient
from app.main.blueprints.deputydev_cli.app.managers.features.base_feature_handler import (
    BaseFeatureHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    FeatureHandlingRedirections,
    FeatureHandlingResult,
    FeatureNextAction,
    PlainTextQuery,
    PRConfig,
    RegisteredRepo,
    TextSelectionQuery,
)


class IterativeChatHandler(BaseFeatureHandler):
    def __init__(
        self,
        process_executor: ProcessPoolExecutor,
        query: Union[PlainTextQuery, TextSelectionQuery],
        one_dev_client: OneDevClient,
        local_repo: BaseLocalRepo,
        weaviate_client: WeaviateSyncAndAsyncClients,
        embedding_manager: BaseEmbeddingManager,
        chunkable_files_with_hashes: Dict[str, str],
        auth_token: str,
        pr_config: Optional[PRConfig] = None,
        session_id: Optional[str] = None,
        apply_diff: bool = False,
        registered_repo_details: Optional[RegisteredRepo] = None,
    ):
        super().__init__(
            process_executor=process_executor,
            query=query,
            one_dev_client=one_dev_client,
            local_repo=local_repo,
            weaviate_client=weaviate_client,
            embedding_manager=embedding_manager,
            chunkable_files_with_hashes=chunkable_files_with_hashes,
            auth_token=auth_token,
            pr_config=pr_config,
            session_id=session_id,
            apply_diff=apply_diff,
            registered_repo_details=registered_repo_details,
        )

    async def validate_and_set_final_payload(self) -> None:
        if not isinstance(self.query, PlainTextQuery):
            raise ValueError(f"Expected {PlainTextQuery.__name__} but got {type(self.query).__name__}")

        if not self.session_id:
            raise ValueError("Session ID is required for iterative chat")

        final_payload: Dict[str, Any] = dict()
        final_payload["query"] = self.query.text

        self.final_payload = final_payload
        self.final_headers: Dict[str, str] = {"X-Session-Id": self.session_id}

        self.redirections = FeatureHandlingRedirections(
            success_redirect=FeatureNextAction.CONTINUE_CHAT,
            error_redirect=FeatureNextAction.CONTINUE_CHAT,
        )

    async def handle_feature(self) -> FeatureHandlingResult:
        if not self.final_payload:
            await self.validate_and_set_final_payload()

        headers = {
            **self.final_headers,
            "Authorization": f"Bearer {self.auth_token}",
        }

        chat_history_response = await self.one_dev_client.fetch_relevant_chat_history(
            payload={"query": self.query.text},
            headers=headers,
        )

        query_vector = await self.embedding_manager.embed_text_array(texts=[self.query.text], store_embeddings=False)
        search_type = SearchTypes.VECTOR_DB_BASED if ConfigManager.configs["USE_VECTOR_DB"] else SearchTypes.NATIVE

        relevant_chunks, _, focus_chunks = await ChunkingManger.get_relevant_chunks(
            query=self.build_query(chat_history_response.get("chats", [])),
            local_repo=self.local_repo,
            embedding_manager=self.embedding_manager,
            process_executor=self.process_executor,
            focus_files=self.query.focus_files,
            focus_chunks=[
                f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}" for chunk in self.query.focus_snippets
            ],
            weaviate_client=self.weaviate_client,
            chunkable_files_with_hashes=self.chunkable_files_with_hashes,
            query_vector=query_vector[0][0],
            search_type=search_type,
            max_chunks_to_return=MAX_ITERATIVE_CHUNKS,
        )
        self.final_payload.update(
            {
                "relevant_chunks": self.handle_relevant_chunks(search_type, relevant_chunks),
                "focus_chunks": self.handle_relevant_chunks(search_type, focus_chunks),
                "is_llm_reranking_enabled": False,
                "relevant_chat_history": chat_history_response.get("chats", []),
            }
        )

        chat_history_response = await self.one_dev_client.iterative_chat(
            payload=self.final_payload,
            headers=headers,
        )

        return FeatureHandlingResult(**chat_history_response, redirections=self.redirections)

    def build_query(self, previous_chats: List[dict]):
        query = self.query.text
        for chat in previous_chats:
            query += f"{chat['query']} \n  {chat['response']}"
        return query
