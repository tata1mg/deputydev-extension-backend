import time
import uuid
import webbrowser
from typing import Any, Dict, Tuple, Union

import keyring
from prompt_toolkit import PromptSession, print_formatted_text

from app.common.utils.app_logger import AppLogger
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputydev_cli.app.exceptions.exceptions import InvalidVersionException
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

    def store_auth_token(self, token: str):
        """Stores the auth_token securely using keyring."""
        keyring.set_password("my_application", "auth_token", token)

    def load_auth_token(self) -> Union[str, None]:
        """Loads the auth_token securely using keyring."""
        return keyring.get_password("my_application", "auth_token")

    async def poll_session(self, device_code: str):
        """Polls the session for authentication status."""
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
                if "error" not in response:
                    if not response.get("jwt_token") or response.get("jwt_token") is None:
                        raise Exception("No JWT token found in response")
                    self.app_context.auth_token = response["jwt_token"]
                    # Storing jwt token in user's machine using keyring
                    self.store_auth_token(self.app_context.auth_token)
                    return self.app_context, ScreenType.DEFAULT  # Exit on success
                else:
                    print_formatted_text("Authentication is in progress. Please wait...")

            except Exception as e:
                print_formatted_text(f"Polling error: {e}")

            time.sleep(3)

        # If we reach here, it means authentication failed
        print_formatted_text("Authentication failed, please try again later.")
        return self.app_context, ScreenType.HOME

    async def verify_current_session(self) -> bool:
        """Attempts to authenticate the user using the provided auth token."""

        # Extracting auth token from user's machine
        auth_token = self.load_auth_token()

        if not auth_token:
            return False

        try:
            print_formatted_text("Verifying the auth token...")
            response = await self.app_context.one_dev_client.verify_auth_token(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {auth_token}",
                }
            )
            # Check if the response contains a status of 'verified'
            if response["status"] == "VERIFIED":
                return True
            else:
                print_formatted_text("Session is expired. Please login again!")
                return False

        except InvalidVersionException:
            print_formatted_text(f"An error occurred during authentication. Please login again!")
            return False

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        print_formatted_text("Welcome to DeputyDev CLI!")

        # Check if the current session is present and valid
        is_current_session_present_and_valid = await self.verify_current_session()
        if is_current_session_present_and_valid:
            self.app_context.auth_token = self.load_auth_token()
            print("You are now logged in. Redirecting to the main interface...")
            return self.app_context, ScreenType.DEFAULT

        # If the current session is not present or is not valid, initiate login
        device_code = str(uuid.uuid4())
        is_external_auth_request = "true"

        auth_url = f"{ConfigManager.configs['FRONTEND_URL']}/external-auth?device_code={device_code}&is_external_auth_request={is_external_auth_request}"
        print_formatted_text(f"Please visit this link for authentication: {auth_url}")

        # Open the URL in the default web browser
        webbrowser.open(auth_url)

        # Polling session
        return await self.poll_session(device_code)
