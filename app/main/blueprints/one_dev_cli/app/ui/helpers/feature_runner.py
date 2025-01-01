import asyncio
from typing import Optional, Tuple

from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts.progress_bar import ProgressBar, formatters

from app.main.blueprints.one_dev_cli.app.constants.cli import CLIFeatures
from app.main.blueprints.one_dev_cli.app.managers.features.dataclasses.main import (
    FeatureNextAction,
    FinalSuccessJob,
)
from app.main.blueprints.one_dev_cli.app.managers.features.factory import FeatureFactory
from app.main.blueprints.one_dev_cli.app.ui.helpers.feature_response_handler import (
    FeatureResponseHandler,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import AppContext


class FeatureRunner:
    def __init__(self, app_context: AppContext):
        self.app_context = app_context
        self.feature_labels = {
            CLIFeatures.CODE_GENERATION: "Generating code",
            CLIFeatures.DOCS_GENERATION: "Generating documentation",
            CLIFeatures.TEST_GENERATION: "Generating tests",
            CLIFeatures.TASK_PLANNER: "Planning",
            CLIFeatures.ITERATIVE_CHAT: "Thinking",
            CLIFeatures.GENERATE_AND_APPLY_DIFF: "Generating diff" if not self.app_context.pr_config else "Creating PR",
        }

    async def run_feature(self) -> Tuple[FeatureNextAction, Optional[str]]:
        if (
            self.app_context.operation is not None
            and self.app_context.query is not None
            and self.app_context.local_repo is not None
            and self.app_context.weaviate_client is not None
            and self.app_context.embedding_manager is not None
            and self.app_context.chunkable_files_with_hashes is not None
            and self.app_context.auth_token is not None
            and self.app_context.local_user_details is not None
            and self.app_context.process_executor is not None
        ):
            tasks = [
                asyncio.create_task(
                    FeatureFactory.handle_feature(
                        process_executor=self.app_context.process_executor,
                        local_user_details=self.app_context.local_user_details,
                        feature=self.app_context.operation,
                        query=self.app_context.query,
                        one_dev_client=self.app_context.one_dev_client,
                        local_repo=self.app_context.local_repo,
                        weaviate_client=self.app_context.weaviate_client,
                        embedding_manager=self.app_context.embedding_manager,
                        chunkable_files_with_hashes=self.app_context.chunkable_files_with_hashes,
                        auth_token=self.app_context.auth_token,
                        pr_config=self.app_context.pr_config,
                        session_id=self.app_context.session_id,
                        registered_repo_details=self.app_context.registered_repo_details,
                    )
                )
            ]

            with patch_stdout():
                with ProgressBar(
                    formatters=[
                        formatters.Label(),
                        formatters.Text(" "),
                        formatters.Bar(),
                        formatters.Text(" "),
                    ]
                ) as pb:
                    for feature_task in pb(
                        asyncio.as_completed(tasks),
                        label=self.feature_labels.get(self.app_context.operation, "Brainstorming ..."),
                    ):
                        resp = await feature_task
                        await FeatureResponseHandler(
                            feature_response=resp,
                            app_context=self.app_context,
                        ).handle_response()
                        return resp.next_action, (resp.session_id if isinstance(resp, FinalSuccessJob) else None)

        raise ValueError("Invalid app context to run feature")
