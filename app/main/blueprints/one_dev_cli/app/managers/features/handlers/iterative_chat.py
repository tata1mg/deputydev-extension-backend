from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, Optional, Union

from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
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


class IterativeChatHandler(BaseFeatureHandler):
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
        if self.local_user_details.email:
            headers["X-User-Email"] = self.local_user_details.email
        if self.local_user_details.name:
            headers["X-User-Name"] = self.local_user_details.name
        api_response = await self.one_dev_client.iterative_chat(
            payload=self.final_payload,
            headers=headers,
        )
        return FeatureHandlingResult(**api_response, redirections=self.redirections)
