from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, Optional, Union

from app.common.services.chunking.chunking_manager import ChunkingManger
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repo.local_repo.managers.git_repo import GitRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.one_dev_cli.app.clients.one_dev import OneDevClient
from app.main.blueprints.one_dev_cli.app.managers.features.base_feature_handler import (
    BaseFeatureHandler,
)
from app.main.blueprints.one_dev_cli.app.managers.features.dataclasses.main import (
    FeatureHandlingRedirections,
    FeatureHandlingResult,
    FeatureNextAction,
    LocalUserDetails,
    PlainTextQuery,
    PRConfig,
    RegisteredRepo,
    TextSelectionQuery,
)


class CodeGenerationHandler(BaseFeatureHandler):
    def __init__(
        self,
        process_executor: ProcessPoolExecutor,
        local_user_details: LocalUserDetails,
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
        usage_hash: Optional[str] = None,
    ):
        super().__init__(
            process_executor=process_executor,
            local_user_details=local_user_details,
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
            usage_hash=usage_hash,
        )

    async def validate_and_set_final_payload(self):
        if not isinstance(self.query, PlainTextQuery):
            raise ValueError(f"Expected {PlainTextQuery.__name__} but got {type(self.query).__name__}")

        final_payload: Dict[str, Any] = dict()

        final_payload["query"] = self.query.text

        if self.pr_config and self.registered_repo_details and isinstance(self.local_repo, GitRepo):
            final_payload["create_pr"] = True
            final_payload["pr_config"] = dict(
                source_branch=self.pr_config.source_branch,
                destination_branch=self.pr_config.destination_branch,
                pr_title_prefix=self.pr_config.pr_title_prefix,
                commit_message_prefix=self.pr_config.commit_message_prefix,
                repo_id=self.registered_repo_details.repo_id,
                parent_source_branch=self.local_repo.get_active_branch(),
            )

        if self.apply_diff:
            final_payload["apply_diff"] = True

        query_vector = await self.embedding_manager.embed_text_array(texts=[self.query.text], store_embeddings=False)

        relevant_chunks, _ = await ChunkingManger.get_relevant_chunks(
            query=self.query.text,
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
            search_type=SearchTypes.VECTOR_DB_BASED if ConfigManager.configs["USE_VECTOR_DB"] else SearchTypes.NATIVE,
            usage_hash=self.usage_hash,
        )

        final_payload["relevant_chunks"] = relevant_chunks

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

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
        }
        if self.local_user_details.email:
            headers["X-User-Email"] = self.local_user_details.email
        if self.local_user_details.name:
            headers["X-User-Name"] = self.local_user_details.name
        api_response = await self.one_dev_client.generate_code(
            payload=self.final_payload,
            headers=headers,
        )

        return FeatureHandlingResult(**api_response, redirections=self.redirections)
