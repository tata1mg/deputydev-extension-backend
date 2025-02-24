from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional, Union

from deputydev_core.clients.http.service_clients.one_dev_client import OneDevClient
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


class DiffGenerationHandler(BaseFeatureHandler):
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
        if not self.session_id:
            raise ValueError("Session ID is required for diff generation")
        self.final_headers: Dict[str, str] = {"X-Session-Id": self.session_id}
        self.redirections = FeatureHandlingRedirections(
            success_redirect=FeatureNextAction.HOME_SCREEN,
            error_redirect=FeatureNextAction.CONTINUE_CHAT,
        )
        final_payload = {}

        if self.pr_config and self.registered_repo_details and isinstance(self.local_repo, GitRepo):
            final_payload["pr_config"] = dict(
                source_branch=self.pr_config.source_branch,
                destination_branch=self.pr_config.destination_branch,
                pr_title_prefix=self.pr_config.pr_title_prefix,
                commit_message_prefix=self.pr_config.commit_message_prefix,
                workspace_id=self.registered_repo_details.workspace_id,
                repo_name=self.registered_repo_details.repo_name,
                parent_source_branch=self.local_repo.get_active_branch(),
            )

        self.final_payload = final_payload

    async def handle_feature(self) -> FeatureHandlingResult:
        headers = {
            **self.final_headers,
            "Authorization": f"Bearer {self.auth_token}",
        }
        api_response = await self.one_dev_client.generate_diff(
            payload=self.final_payload,
            headers=headers,
        )
        return FeatureHandlingResult(**api_response, redirections=self.redirections)
