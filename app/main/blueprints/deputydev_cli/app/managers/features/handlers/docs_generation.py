from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, Optional, Union

from app.common.services.chunking.chunking_manager import ChunkingManger
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputydev_cli.app.clients.one_dev import OneDevClient
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


class DocsGenerationHandler(BaseFeatureHandler):
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

    async def validate_and_set_final_payload(self):
        if not isinstance(self.query, TextSelectionQuery):
            raise ValueError(f"Expected {TextSelectionQuery.__name__} but got {type(self.query).__name__}")

        final_payload: Dict[str, Any] = dict()

        if self.pr_config:
            final_payload["create_pr"] = True
            final_payload["pr_config"] = dict(
                destination_branch=self.pr_config.destination_branch,
                pr_title_prefix=self.pr_config.pr_title_prefix,
                commit_message_prefix=self.pr_config.commit_message_prefix,
            )

        selected_text = self._get_selected_text(self.query).get_xml()
        query = selected_text + ("   \n  " + self.query.custom_instructions if self.query.custom_instructions else "")
        final_payload["query"] = selected_text
        if self.query.custom_instructions:
            final_payload["custom_instructions"] = self.query.custom_instructions

        query_vector = await self.embedding_manager.embed_text_array(texts=[query], store_embeddings=False)
        search_type = SearchTypes.VECTOR_DB_BASED if ConfigManager.configs["USE_VECTOR_DB"] else SearchTypes.NATIVE
        relevant_chunks, _ = await ChunkingManger.get_relevant_chunks(
            query=query,
            local_repo=self.local_repo,
            embedding_manager=self.embedding_manager,
            process_executor=self.process_executor,
            focus_files=[],
            focus_chunks=[],
            weaviate_client=self.weaviate_client,
            chunkable_files_with_hashes=self.chunkable_files_with_hashes,
            query_vector=query_vector[0][0],
            search_type=search_type,
        )

        final_payload["relevant_chunks"] = self.handle_relevant_chunks(search_type, relevant_chunks)

        self.final_payload = final_payload

        self.redirections = FeatureHandlingRedirections(
            success_redirect=FeatureNextAction.CONTINUE_CHAT
            if not (self.pr_config or self.apply_diff)
            else FeatureNextAction.HOME_SCREEN,
            error_redirect=FeatureNextAction.ERROR_OUT_AND_END,
        )

    async def handle_feature(self) -> FeatureHandlingResult:

        if not self.final_payload:
            await self.validate_and_set_final_payload()
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        api_response = await self.one_dev_client.generate_docs(
            payload=self.final_payload,
            headers=headers,
        )
        return FeatureHandlingResult(**api_response, redirections=self.redirections)
