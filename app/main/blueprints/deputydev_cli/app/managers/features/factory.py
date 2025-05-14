import asyncio
import traceback
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional, Type, Union

from deputydev_core.services.embedding.base_embedding_manager import (
    BaseEmbeddingManager,
)
from deputydev_core.services.repo.local_repo.base_local_repo_service import (
    BaseLocalRepo,
)
from deputydev_core.services.repository.dataclasses.main import (
    WeaviateSyncAndAsyncClients,
)
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.exceptions import InvalidVersionException

from app.main.blueprints.deputydev_cli.app.clients.one_dev_cli_client import (
    OneDevCliClient,
)
from app.main.blueprints.deputydev_cli.app.constants.cli import CLIFeatures
from app.main.blueprints.deputydev_cli.app.managers.features.base_feature_handler import (
    BaseFeatureHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    FinalFailedJob,
    FinalSuccessJob,
    PlainTextQuery,
    PRConfig,
    RegisteredRepo,
    TextSelectionQuery,
)
from app.main.blueprints.deputydev_cli.app.managers.features.handlers.code_generation import (
    CodeGenerationHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.handlers.code_plan_generation import (
    CodePlanGenerationHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.handlers.docs_generation import (
    DocsGenerationHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.handlers.generate_and_apply_diff import (
    DiffGenerationHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.handlers.iterative_chat import (
    IterativeChatHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.handlers.plan_to_code import (
    PlanCodeGenerationHandler,
)
from app.main.blueprints.deputydev_cli.app.managers.features.handlers.test_case_generation import (
    TestCaseGenerationHandler,
)


class FeatureFactory:
    feature_handler_map: Dict[CLIFeatures, Type[BaseFeatureHandler]] = {
        CLIFeatures.CODE_GENERATION: CodeGenerationHandler,
        CLIFeatures.TEST_GENERATION: TestCaseGenerationHandler,
        CLIFeatures.DOCS_GENERATION: DocsGenerationHandler,
        CLIFeatures.TASK_PLANNER: CodePlanGenerationHandler,
        CLIFeatures.ITERATIVE_CHAT: IterativeChatHandler,
        CLIFeatures.GENERATE_AND_APPLY_DIFF: DiffGenerationHandler,
        CLIFeatures.PLAN_CODE_GENERATION: PlanCodeGenerationHandler,
    }

    @classmethod
    async def handle_feature(
        cls,
        feature: CLIFeatures,
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
        registered_repo_details: Optional[RegisteredRepo] = None,
    ) -> Union[FinalSuccessJob, FinalFailedJob]:
        handler = cls.feature_handler_map[feature](
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
            registered_repo_details=registered_repo_details,
        )
        try:
            await handler.validate_and_set_final_payload()
            feature_job = await handler.handle_feature()
        except InvalidVersionException as ex:
            return FinalFailedJob(display_message=str(ex))

        # poll for the job status
        while True:
            try:
                job_status = await one_dev_client.get_job_status(
                    payload={"job_id": feature_job.job_id},
                    headers={
                        "Authorization": f"Bearer {auth_token}",
                        "X-Session-Id": feature_job.session_id,
                    },
                )
                if job_status.get("status") == "SUCCESS":
                    return FinalSuccessJob(
                        **job_status["response"],
                        next_action=feature_job.redirections.success_redirect,
                        job_id=feature_job.job_id,
                    )
                elif job_status.get("status") == "FAILED":
                    return FinalFailedJob(
                        display_message=job_status["response"]["message"],
                        next_action=feature_job.redirections.error_redirect,
                        job_id=feature_job.job_id,
                    )
            except Exception:
                AppLogger.log_debug(traceback.format_exc())
                return FinalFailedJob(display_message="Your request to the server failed. Please try again later.")
            await asyncio.sleep(ConfigManager.configs["POLLING_INTERVAL"])
