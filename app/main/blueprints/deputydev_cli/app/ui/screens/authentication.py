import time
import uuid
from typing import Any, Dict, Optional, Tuple

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.validation import ValidationError

from app.common.constants.constants import AuthStatus
from app.common.utils.app_logger import AppLogger
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputydev_cli.app.clients.browser import BrowserClient
from app.main.blueprints.deputydev_cli.app.exceptions.exceptions import (
    InvalidVersionException,
)
from app.main.blueprints.deputydev_cli.app.managers.keyring.auth_token_keyring import (
    AuthTokenKeyRing,
)
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

    async def poll_session(self, supabase_session_id: str):
        """Polls the session for authentication status."""

        print_formatted_text("Authentication is in progress. Please wait...")
        max_attempts = 60
        for attempt in range(max_attempts):
            try:
                response = await self.app_context.one_dev_client.get_session(
                    headers={
                        "Content-Type": "application/json",
                        "X-Supabase-Session-Id": supabase_session_id,
                    }
                )

                if response.get("status") == AuthStatus.AUTHENTICATED.value:
                    if not response.get("encrypted_session_data") or response.get("encrypted_session_data") is None:
                        raise Exception("No encrypted session data found in response")
                    self.app_context.auth_token = response["encrypted_session_data"]
                    # Storing jwt token in user's machine using keyring
                    AuthTokenKeyRing.store_auth_token(self.app_context.auth_token)
                    return self.app_context, ScreenType.DEFAULT  # Exit on success
                time.sleep(3)  # Wait for 3 seconds before polling again
            except Exception as e:
                AppLogger.log_debug(f"Error polling session: {e}")
                time.sleep(1)  # Wait for 1 second on exception

        # If we reach here, it means authentication failed
        print_formatted_text("Authentication failed, please try again later.")
        return self.app_context, ScreenType.HOME

    async def verify_current_session(self) -> bool:
        """Attempts to authenticate the user using the provided auth token."""

        # Extracting auth token from user's machine
        auth_token = AuthTokenKeyRing.load_auth_token()

        if not auth_token:
            return False

        try:
            response = await self.app_context.one_dev_client.verify_auth_token(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {auth_token}",
                }
            )
            # Check if the response contains a status of 'verified'
            if response["status"] == AuthStatus.VERIFIED.value:
                self.app_context.auth_token = AuthTokenKeyRing.load_auth_token()
                return True
            else:
                print_formatted_text("Session is expired. Please login again!")
                return False

        except InvalidVersionException as ex:
            raise ValidationError(message=str(ex))
        except Exception:
            print_formatted_text("Authentication failed, please try again later.")
            return False

    async def update_configs(self, redirect_screen: ScreenType) -> ScreenType:
        """
        Fetches the essential configs and updates the ConfigManager with the fetched configs.
        Args:
            redirect_screen (ScreenType): The screen to redirect to after fetching the configs.
        Returns:
            ScreenType: The screen to redirect to after fetching the configs.
        """
        try:
            ConfigManager.initialize(in_memory=True)
            configs: Optional[Dict[str, str]] = await self.app_context.one_dev_client.get_configs(
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.app_context.auth_token}"}
            )
            if configs is None:
                raise Exception("No configs fetched")
            ConfigManager.set(configs)
            return redirect_screen
        except Exception:
            print_formatted_text("Failed to fetch configs")
            return ScreenType.HOME

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        print_formatted_text("Welcome to DeputyDev CLI!")

        # Check if the current session is present and valid
        is_current_session_present_and_valid = await self.verify_current_session()
        redirect_screen: ScreenType

        if is_current_session_present_and_valid:
            redirect_screen = await self.update_configs(ScreenType.DEFAULT)
            return self.app_context, redirect_screen

        # If the current session is not present or is not valid, initiate login
        supabase_session_id = str(uuid.uuid4())
        BrowserClient.initiate_cli_login(supabase_session_id)

        # Polling session
        app_context_to_return, redirect_screen = await self.poll_session(supabase_session_id)
        redirect_screen = await self.update_configs(redirect_screen)
        return app_context_to_return, redirect_screen
