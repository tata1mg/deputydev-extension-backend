from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, Optional, Union

from deputydev_core.services.chunking.chunking_manager import ChunkingManger
from deputydev_core.services.embedding.base_embedding_manager import (
    BaseEmbeddingManager,
)
from deputydev_core.services.repo.local_repo.base_local_repo_service import (
    BaseLocalRepo,
)
from deputydev_core.services.repo.local_repo.managers.git_repo_service import GitRepo
from deputydev_core.services.repository.dataclasses.main import (
    WeaviateSyncAndAsyncClients,
)
from deputydev_core.services.search.dataclasses.main import SearchTypes
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.constants.constants import (
    IS_LLM_RERANKING_ENABLED,
    MAX_RELEVANT_CHUNKS,
)
from app.main.blueprints.deputydev_cli.app.clients.one_dev_cli_client import (
    OneDevCliClient,
)
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
        one_dev_client: OneDevCliClient,
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

        if self.pr_config and self.registered_repo_details and isinstance(self.local_repo, GitRepo):
            final_payload["create_pr"] = True
            final_payload["pr_config"] = dict(
                source_branch=self.pr_config.source_branch,
                destination_branch=self.pr_config.destination_branch,
                pr_title_prefix=self.pr_config.pr_title_prefix,
                commit_message_prefix=self.pr_config.commit_message_prefix,
                workspace_id=self.registered_repo_details.workspace_id,
                repo_name=self.registered_repo_details.repo_name,
                parent_source_branch=self.local_repo.get_active_branch(),
            )

        selected_text = self._get_selected_text(self.query).get_xml()
        query = selected_text + ("   \n  " + self.query.custom_instructions if self.query.custom_instructions else "")
        final_payload["query"] = selected_text
        if self.query.custom_instructions:
            final_payload["custom_instructions"] = self.query.custom_instructions

        query_vector = await self.embedding_manager.embed_text_array(texts=[query], store_embeddings=False)
        search_type = SearchTypes.VECTOR_DB_BASED if ConfigManager.configs["USE_VECTOR_DB"] else SearchTypes.NATIVE
        relevant_chunks, _, focus_chunks = await ChunkingManger.get_relevant_chunks(
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
            max_chunks_to_return=MAX_RELEVANT_CHUNKS,
        )

        final_payload.update(
            {
                "relevant_chunks": self.handle_relevant_chunks(search_type, relevant_chunks),
                "focus_chunks": self.handle_relevant_chunks(search_type, focus_chunks),
                "is_llm_reranking_enabled": IS_LLM_RERANKING_ENABLED,
            }
        )

        self.final_payload = final_payload

        self.redirections = FeatureHandlingRedirections(
            success_redirect=(
                FeatureNextAction.CONTINUE_CHAT
                if not (self.pr_config or self.apply_diff)
                else FeatureNextAction.HOME_SCREEN
            ),
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
