from typing import Any, Dict, Tuple

from prompt_toolkit import PromptSession

from app.common.utils.app_logger import AppLogger
from app.main.blueprints.deputydev_cli.app.managers.authentication.authentication_manager import AuthenticationManager
from app.main.blueprints.deputydev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)


class Authentication(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.AUTHENTICATION

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        # Check if the current session is present and valid
        try:
            authentication_manager = AuthenticationManager(
                self.app_context.one_dev_client, self.session
            )
            self.app_context.auth_token = await authentication_manager.authenticate_and_get_auth_token()
            return self.app_context, ScreenType.DEFAULT
        except Exception as e:
            AppLogger.log_debug(f"Error authenticating user: {e}")
            return self.app_context, ScreenType.EXIT
