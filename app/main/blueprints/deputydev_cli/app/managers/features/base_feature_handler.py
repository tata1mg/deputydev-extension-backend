import os
from abc import ABC
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional, Union

from app.common.constants.constants import NO_OF_CHUNKS_FOR_LLM
from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.chunking.utils.snippet_renderer import render_snippet_array
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.services.search.dataclasses.main import SearchTypes
from app.common.utils.file_utils import read_file
from app.main.blueprints.deputydev_cli.app.clients.one_dev import OneDevClient
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    FeatureHandlingRedirections,
    FeatureHandlingResult,
    FeatureNextAction,
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
        self.process_executor = process_executor
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
        self.usage_hash = usage_hash

        self.redirections: FeatureHandlingRedirections = FeatureHandlingRedirections(
            success_redirect=FeatureNextAction.ERROR_OUT_AND_END,
            error_redirect=FeatureNextAction.ERROR_OUT_AND_END,
        )

    def _get_selected_text(self, text_selection_query: TextSelectionQuery) -> ChunkInfo:
        abs_filepath = os.path.join(self.local_repo.repo_path, text_selection_query.file_path)
        file_content = read_file(abs_filepath)

        if text_selection_query.start_line is None or text_selection_query.end_line is None:
            return ChunkInfo(
                content=file_content,
                source_details=ChunkSourceDetails(
                    file_path=text_selection_query.file_path,
                    file_hash="",
                    start_line=1,
                    end_line=len(file_content.splitlines()),
                ),
            )
        line_wise_file_content = file_content.splitlines()
        selected_text = "\n".join(
            line_wise_file_content[text_selection_query.start_line - 1 : text_selection_query.end_line]
        )
        return ChunkInfo(
            content=selected_text,
            source_details=ChunkSourceDetails(
                file_path=text_selection_query.file_path,
                file_hash="",
                start_line=text_selection_query.start_line,
                end_line=text_selection_query.end_line,
            ),
        )

    async def handle_feature(self) -> FeatureHandlingResult:
        raise NotImplementedError(self.NOT_IMPLEMENTED_MSG)

    async def validate_and_set_final_payload(self) -> None:
        raise NotImplementedError(self.NOT_IMPLEMENTED_MSG)

    @classmethod
    def handle_relevant_chunks(cls, search_type, chunks):
        if search_type == SearchTypes.VECTOR_DB_BASED:
            return render_snippet_array(chunks)
        else:
            return render_snippet_array(chunks[:NO_OF_CHUNKS_FOR_LLM])
