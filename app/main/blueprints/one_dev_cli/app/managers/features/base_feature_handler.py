import os
from abc import ABC
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional, Union

from weaviate import WeaviateAsyncClient

from app.common.services.chunking.chunking_handler import read_file
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.main.blueprints.one_dev_cli.app.clients.one_dev import OneDevClient
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


class BaseFeatureHandler(ABC):
    NOT_IMPLEMENTED_MSG = "Subclasses must implement this method"

    def __init__(
        self,
        process_executor: ProcessPoolExecutor,
        local_user_details: LocalUserDetails,
        query: Union[PlainTextQuery, TextSelectionQuery],
        one_dev_client: OneDevClient,
        local_repo: BaseLocalRepo,
        weaviate_client: WeaviateAsyncClient,
        embedding_manager: BaseEmbeddingManager,
        chunkable_files_with_hashes: Dict[str, str],
        auth_token: str,
        pr_config: Optional[PRConfig] = None,
        session_id: Optional[str] = None,
        apply_diff: bool = False,
        registered_repo_details: Optional[RegisteredRepo] = None,
    ):
        self.process_executor = process_executor
        self.local_user_details = local_user_details
        self.query = query
        self.one_dev_client = one_dev_client
        self.local_repo = local_repo
        self.auth_token = auth_token
        self.weaviate_client = weaviate_client
        self.chunkable_files_with_hashes = chunkable_files_with_hashes
        self.embedding_manager = embedding_manager
        self.pr_config = pr_config
        self.session_id = session_id
        self.apply_diff = apply_diff
        self.registered_repo_details = registered_repo_details

        self.redirections: FeatureHandlingRedirections = FeatureHandlingRedirections(
            success_redirect=FeatureNextAction.ERROR_OUT_AND_END,
            error_redirect=FeatureNextAction.ERROR_OUT_AND_END,
        )

    def _get_selected_text(self, text_selection_query: TextSelectionQuery) -> str:
        abs_filepath = os.path.join(self.local_repo.repo_path, text_selection_query.file_path)
        file_content = read_file(abs_filepath)

        if text_selection_query.start_line is None or text_selection_query.end_line is None:
            return file_content
        line_wise_file_content = file_content.splitlines()
        selected_text = "\n".join(
            line_wise_file_content[text_selection_query.start_line - 1 : text_selection_query.end_line]
        )
        return selected_text

    async def handle_feature(self) -> FeatureHandlingResult:
        raise NotImplementedError(self.NOT_IMPLEMENTED_MSG)

    async def validate_and_set_final_payload(self) -> None:
        raise NotImplementedError(self.NOT_IMPLEMENTED_MSG)
