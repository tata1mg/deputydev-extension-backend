from typing import Any, Coroutine, Dict, Optional, Tuple, Union

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.patch_stdout import patch_stdout

from app.main.blueprints.one_dev_cli.app.constants.cli import CLIFeatures
from app.main.blueprints.one_dev_cli.app.managers.features.dataclasses.main import (
    FeatureNextAction,
    PlainTextQuery,
)
from app.main.blueprints.one_dev_cli.app.ui.dataclasses.main import FlowStatus
from app.main.blueprints.one_dev_cli.app.ui.helpers.feature_runner import FeatureRunner
from app.main.blueprints.one_dev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.pr_config_selection import (
    PRConfigSelection,
)


class ChatScreen(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[
            Union[str, Coroutine[Any, Any, Tuple[FeatureNextAction, Optional[str]]]]
        ] = PromptSession()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.CHAT

    def bottom_toolbar(self):
        if self.app_context.current_status in [FlowStatus.INITIALIZED, FlowStatus.DIFF_APPLIED, FlowStatus.PR_CREATED]:
            return HTML("[^C]Exit")
        if self.app_context.current_status == FlowStatus.CODE_GENERATED:
            if self.app_context.registered_repo_details:
                return HTML("[^C]Exit    [^P]Create PR    [^D]Apply Diff")
            return HTML("[^C]Exit    [^D]Apply Diff")
        if self.app_context.current_status == FlowStatus.PLAN_GENERATED:
            return HTML("[^C]Exit    [^D]Generate code from plan")

    async def fetch_pr_config_and_create_pr(self):
        self.app_context.operation = CLIFeatures.GENERATE_AND_APPLY_DIFF
        self.app_context, _redirect_screen = await PRConfigSelection(self.app_context).render(pr_to_be_created=True)
        return await FeatureRunner(self.app_context).run_feature()

    async def get_bindings(
        self,
    ):
        bindings = KeyBindings()

        if self.app_context.current_status == FlowStatus.CODE_GENERATED:

            @bindings.add("c-d")
            async def _(event: KeyPressEvent):
                self.app_context.operation = CLIFeatures.GENERATE_AND_APPLY_DIFF
                app = event.app
                app.exit(result=FeatureRunner(self.app_context).run_feature())

            if self.app_context.registered_repo_details:

                @bindings.add("c-p")
                async def _(event: KeyPressEvent):
                    app = event.app
                    app.exit(result=self.fetch_pr_config_and_create_pr())

        elif self.app_context.current_status == FlowStatus.PLAN_GENERATED:

            @bindings.add("c-d")
            async def _(event: KeyPressEvent):
                self.app_context.operation = CLIFeatures.PLAN_CODE_GENERATION
                app = event.app
                app.exit(result=FeatureRunner(self.app_context).run_feature())

        return bindings

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        with patch_stdout():
            message: Union[
                str, Coroutine[Any, Any, Tuple[FeatureNextAction, Optional[str]]]
            ] = await self.session.prompt_async(
                "You: ",
                bottom_toolbar=self.bottom_toolbar,
                key_bindings=await self.get_bindings(),
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
