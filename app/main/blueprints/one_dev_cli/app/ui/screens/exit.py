from typing import Any, Dict, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from app.main.blueprints.one_dev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)


class Exit(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.EXIT

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        with patch_stdout():
            await self.session.prompt_async("Press any key to exit ... ")
        return self.app_context, ScreenType.DEFAULT
