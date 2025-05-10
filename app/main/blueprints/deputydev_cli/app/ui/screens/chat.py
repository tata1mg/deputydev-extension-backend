from typing import Any, Coroutine, Dict, Optional, Tuple, Union

from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.feedbacks import UpvoteDownvoteFeedbacks
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.patch_stdout import patch_stdout

from app.main.blueprints.deputydev_cli.app.constants.cli import CLIFeatures
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    FeatureNextAction,
    PlainTextQuery,
)
from app.main.blueprints.deputydev_cli.app.ui.dataclasses.main import FlowStatus
from app.main.blueprints.deputydev_cli.app.ui.helpers.feature_runner import (
    FeatureRunner,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.exit import Exit
from app.main.blueprints.deputydev_cli.app.ui.screens.pr_config_selection import (
    PRConfigSelection,
)


class ChatScreen(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[Union[str, Coroutine[Any, Any, Tuple[FeatureNextAction, Optional[str]]]]] = (
            PromptSession()
        )

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.CHAT

    def bottom_toolbar(self):
        if self.app_context.current_status in [FlowStatus.INITIALIZED, FlowStatus.DIFF_APPLIED, FlowStatus.PR_CREATED]:
            return HTML("[^C]Exit")
        if self.app_context.current_status == FlowStatus.CODE_GENERATED:
            if self.app_context.registered_repo_details:
                toolbar_text = "[^C]Exit    "
                if CLIFeatures.GENERATE_AND_APPLY_DIFF.value in ConfigManager.configs["ENABLED_FEATURES"]:
                    toolbar_text += "[^D]Apply Diff    "
                if "PR_CREATION_ENABLED" in ConfigManager.configs and ConfigManager.configs["PR_CREATION_ENABLED"]:
                    toolbar_text += "[^P]Create PR    "
                toolbar_text += "Is this helpful?: [^W]👍 [^S]👎"
                return HTML(toolbar_text.strip())
            if CLIFeatures.GENERATE_AND_APPLY_DIFF.value in ConfigManager.configs["ENABLED_FEATURES"]:
                return HTML("[^C]Exit    [^D]Apply Diff    Is this helpful?: [^W]👍 [^S]👎")
            return HTML("[^C]Exit")
        if self.app_context.current_status == FlowStatus.PLAN_GENERATED:
            if CLIFeatures.PLAN_CODE_GENERATION.value in ConfigManager.configs["ENABLED_FEATURES"]:
                return HTML("[^C]Exit    [^D]Generate code from plan    Is this helpful?: [^W]👍 [^S]👎")
            return HTML("[^C]Exit")

    async def fetch_pr_config_and_create_pr(self):
        self.app_context.operation = CLIFeatures.GENERATE_AND_APPLY_DIFF
        self.app_context, _redirect_screen = await PRConfigSelection(self.app_context).render(pr_to_be_created=True)
        return await FeatureRunner(self.app_context).run_feature()

    async def get_bindings(
        self,
    ):
        bindings = KeyBindings()

        if self.app_context.current_status == FlowStatus.CODE_GENERATED:
            if CLIFeatures.GENERATE_AND_APPLY_DIFF.value in ConfigManager.configs["ENABLED_FEATURES"]:

                @bindings.add("c-d")
                async def _(event: KeyPressEvent):
                    self.app_context.operation = CLIFeatures.GENERATE_AND_APPLY_DIFF
                    app = event.app
                    app.exit(result=FeatureRunner(self.app_context).run_feature())

            if self.app_context.registered_repo_details:
                if "PR_CREATION_ENABLED" in ConfigManager.configs and ConfigManager.configs["PR_CREATION_ENABLED"]:

                    @bindings.add("c-p")
                    async def _(event: KeyPressEvent):
                        app = event.app
                        app.exit(result=self.fetch_pr_config_and_create_pr())

        elif self.app_context.current_status == FlowStatus.PLAN_GENERATED:
            if CLIFeatures.PLAN_CODE_GENERATION.value in ConfigManager.configs["ENABLED_FEATURES"]:

                @bindings.add("c-d")
                async def _(event: KeyPressEvent):
                    self.app_context.operation = CLIFeatures.PLAN_CODE_GENERATION
                    app = event.app
                    app.exit(result=FeatureRunner(self.app_context).run_feature())

        if self.app_context.current_status in [FlowStatus.PLAN_GENERATED, FlowStatus.CODE_GENERATED]:

            @bindings.add("c-w")
            async def _(event: KeyPressEvent):
                if not self.app_context.session_id or not self.app_context.auth_token:
                    print_formatted_text("Error while recording feedback. Please contact support.")
                    return
                headers = {
                    "Authorization": f"Bearer {self.app_context.auth_token}",
                    "X-Session-Id": self.app_context.session_id,
                }
                try:
                    await self.app_context.one_dev_client.record_feedback(
                        payload={
                            "feedback": UpvoteDownvoteFeedbacks.UPVOTE.value,
                            "job_id": self.app_context.last_operation_job_id,
                        },
                        headers=headers,
                    )
                    print_formatted_text("Thanks for your feedback! 🙏")
                except Exception:
                    print_formatted_text("Error while recording feedback. Please contact support.")

            @bindings.add("c-s")
            async def _(event: KeyPressEvent):
                if not self.app_context.session_id or not self.app_context.auth_token:
                    print_formatted_text("Error while recording feedback. Please contact support.")
                    return
                headers = {
                    "Authorization": f"Bearer {self.app_context.auth_token}",
                    "X-Session-Id": self.app_context.session_id,
                }
                try:
                    await self.app_context.one_dev_client.record_feedback(
                        payload={
                            "feedback": UpvoteDownvoteFeedbacks.DOWNVOTE.value,
                            "job_id": self.app_context.last_operation_job_id,
                        },
                        headers=headers,
                    )
                    print_formatted_text("Thanks for your feedback! 🙏")
                except Exception:
                    print_formatted_text("Error while recording feedback. Please contact support.")

        return bindings

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        if CLIFeatures.ITERATIVE_CHAT.value not in ConfigManager.configs["ENABLED_FEATURES"]:
            return await Exit(app_context=self.app_context).render()
        with patch_stdout():
            message: Union[str, Coroutine[Any, Any, Tuple[FeatureNextAction, Optional[str]]]] = (
                await self.session.prompt_async(
                    "You: ",
                    bottom_toolbar=self.bottom_toolbar,
                    key_bindings=await self.get_bindings(),
                )
            )

            next_action: Optional[FeatureNextAction] = None
            if isinstance(message, str):
                self.app_context.operation = CLIFeatures.ITERATIVE_CHAT
                self.app_context.query = PlainTextQuery(text=message)
                next_action, session_id = await FeatureRunner(self.app_context).run_feature()
                if session_id:
                    self.app_context.session_id = session_id
            else:
                next_action, session_id = await message
                if session_id:
                    self.app_context.session_id = session_id
            if next_action == FeatureNextAction.CONTINUE_CHAT:
                return await self.render()
            elif next_action == FeatureNextAction.ERROR_OUT_AND_END or next_action == FeatureNextAction.HOME_SCREEN:
                return self.app_context, ScreenType.HOME
