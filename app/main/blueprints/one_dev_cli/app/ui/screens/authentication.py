import os
from typing import Any, Dict, Tuple

from git.config import GitConfigParser
from prompt_toolkit import PromptSession
from prompt_toolkit.validation import ValidationError

from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.one_dev_cli.app.exceptions.exceptions import (
    InvalidVersionException,
)
from app.main.blueprints.one_dev_cli.app.managers.features.dataclasses.main import (
    LocalUserDetails,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.common.validators import (
    AsyncValidator,
    validate_existing_text_arg_or_get_input,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)

DEPUTYDEV_AUTH_TOKEN = ConfigManager.configs["AUTH_TOKEN_ENV_VAR"]


class AuthTokenValidator(AsyncValidator):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            raise ValidationError(message="Token cannot be empty")
        try:
            verification_result = await self.app_context.one_dev_client.verify_auth_token(
                payload={"token": input_text},
                headers={"Content-Type": "application/json"},
            )

            if verification_result.get("status") == "VERIFIED":
                return
            else:
                raise ValidationError(message="Auth token is invalid. Please enter a valid auth token.")

        except InvalidVersionException as ex:
            raise ValidationError(message=str(ex))

        except Exception:
            raise ValidationError(message="Auth token verification failed. Please enter a valid auth token.")


class Authentication(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()

    def get_global_git_user(self) -> Tuple[str, str]:
        # Access the Git configuration
        config = GitConfigParser(config_level="global")

        try:
            # Retrieve the global user name and email
            user_name = config.get_value("user", "name")
            user_email = config.get_value("user", "email")
        except Exception:
            user_name, user_email = None, None

        return str(user_name) if user_name else "", str(user_email) if user_email else ""

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.AUTHENTICATION

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        current_auth_token = os.getenv(DEPUTYDEV_AUTH_TOKEN)
        if current_auth_token:
            self.app_context.args.auth_token = current_auth_token
        (self.app_context.auth_token, _is_existing_arg_valid,) = await validate_existing_text_arg_or_get_input(
            session=self.session,
            arg_name="deputydev_auth_token",
            prompt_message=f"Enter your auth token (you can set this in {DEPUTYDEV_AUTH_TOKEN} env variable): ",
            validator=AuthTokenValidator(self.app_context),
            app_context=self.app_context,
            validate_while_typing=False,
        )

        global_user_name, global_user_email = self.get_global_git_user()
        self.app_context.local_user_details = LocalUserDetails(
            name=global_user_name,
            email=global_user_email,
        )

        return self.app_context, ScreenType.DEFAULT
