import os
from typing import Any, Dict, Tuple
import uuid
import requests
import time

from git.config import GitConfigParser
from prompt_toolkit import PromptSession
from prompt_toolkit.validation import ValidationError

from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputydev_cli.app.exceptions.exceptions import (
    InvalidVersionException,
)
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    LocalUserDetails,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.common.validators import (
    AsyncValidator,
    validate_existing_text_arg_or_get_input,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)

DEPUTYDEV_AUTH_TOKEN = ConfigManager.configs["AUTH_TOKEN_ENV_VAR"]
class Authentication(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.AUTHENTICATION

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        # current_auth_token = os.getenv(DEPUTYDEV_AUTH_TOKEN)
        # if current_auth_token:
        #     self.app_context.args.deputydev_auth_token = current_auth_token
        # (self.app_context.auth_token, _is_existing_arg_valid,) = await validate_existing_text_arg_or_get_input(
        #     session=self.session,
        #     arg_name="deputydev_auth_token",
        #     prompt_message=f"Enter your auth token (you can set this in {DEPUTYDEV_AUTH_TOKEN} env variable): ",
        #     validator=AuthTokenValidator(self.app_context),
        #     app_context=self.app_context,
        #     validate_while_typing=False,
        # )

        print("Welcome to DeputyDev CLI!")

        BASE_URL = 'http://localhost:3000'
        device_code = str(uuid.uuid4())
        is_cli = True

        auth_url = f"{BASE_URL}/cli?device_code={device_code}&is_cli={is_cli}"
        print(f"Please vist this link for authentication: {auth_url}")

        max_attempts = 60
        for attempt in range(max_attempts):
            try:
                response = await self.app_context.one_dev_client.get_session(
                    headers={
                        "Content-Type": "application/json",
                        "X-Device-Code": device_code,
                    }
                )

                # Check if the auth token contains an error
                if 'error' not in response:
                    self.app_context.auth_token = response['jwt_token']
                    print("Authentication successful!")
                    print(f"Your auth token is: {self.app_context.auth_token}")
                    return self.app_context, ScreenType.DEFAULT  # Exit on success
                else:
                    print("Authentication is in progress. Please wait...")

            except Exception as e:
                print(f"Polling error: {e}")

            time.sleep(3)

        # If we reach here, it means authentication failed
        print("Authentication failed, please try again later.")
