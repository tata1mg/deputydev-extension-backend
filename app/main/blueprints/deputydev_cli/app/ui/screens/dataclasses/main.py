import argparse
from concurrent.futures import ProcessPoolExecutor
from enum import Enum
from typing import Dict, Optional, Union

from pydantic import BaseModel, ConfigDict

from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.main.blueprints.deputydev_cli.app.clients.one_dev import OneDevClient
from app.main.blueprints.deputydev_cli.app.constants.cli import CLIFeatures
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    PlainTextQuery,
    PRConfig,
    RegisteredRepo,
    TextSelectionQuery,
)
from app.main.blueprints.deputydev_cli.app.managers.initialization.main import (
    InitializationManager,
)
from app.main.blueprints.deputydev_cli.app.ui.dataclasses.main import FlowStatus


class ScreenType(Enum):
    DEFAULT = "DEFAULT"
    HOME = "HOME"
    QUERY_SELECTION = "QUERY_SELECTION"
    AUTHENTICATION = "AUTHENTICATION"
    CHAT = "CHAT"
    REPO_SELECTION = "REPO_SELECTION"
    REPO_INITIALIZATION = "REPO_INITIALIZATION"
    EXIT = "EXIT"
    PR_CONFIG_SELECTION = "PR_CONFIG_SELECTION"


class QueryType(Enum):
    TEXT_SELECTION = "TEXT_SELECTION"
    PLAIN_TEXT = "PLAIN_TEXT"


class AppContext(BaseModel):
    args: argparse.Namespace
    one_dev_client: OneDevClient
    auth_token: Optional[str] = None
    session_id: Optional[str] = None
    local_repo: Optional[BaseLocalRepo] = None
    weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None
    embedding_manager: Optional[BaseEmbeddingManager] = None
    chunkable_files_with_hashes: Optional[Dict[str, str]] = None
    init_manager: Optional[InitializationManager] = None
    query: Optional[Union[PlainTextQuery, TextSelectionQuery]] = None
    operation: Optional[CLIFeatures] = None
    pr_config: Optional[PRConfig] = None
    registered_repo_details: Optional[RegisteredRepo] = None
    process_executor: Optional[ProcessPoolExecutor] = None
    last_operation_job_id: Optional[int] = None

    current_status: FlowStatus = FlowStatus.INITIALIZED

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.one_dev_client:
            await self.one_dev_client.close_session()
        if self.init_manager:
            await self.init_manager.cleanup()
        return True

    def clean_for_new_session(self):
        # Reset the app context for a new session
        self.local_repo = None
        self.query = None
        self.operation = None
        self.pr_config = None
        self.registered_repo_details = None
        self.last_operation_job_id = None
        self.current_status = FlowStatus.INITIALIZED

        # Reset query args except for auth token
        self.args = argparse.Namespace()
        self.args.deputydev_auth_token = self.auth_token
        self.args.clean_cache = False
        self.args.repo_path = None
