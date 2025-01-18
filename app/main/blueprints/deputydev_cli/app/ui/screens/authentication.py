import os
from typing import Any, Dict, Tuple
import uuid
import requests
import time
import keyring

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
from app.main.blueprints.one_dev.routes.end_user.v1.auth import verify_auth_token

DEPUTYDEV_AUTH_TOKEN = ConfigManager.configs["AUTH_TOKEN_ENV_VAR"]
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

    def load_auth_token(self) -> str:
        """Loads the auth_token securely using keyring."""
        return keyring.get_password("my_application", "auth_token")

    async def poll_session(self, device_code: str):
        """Polls the session for authentication status."""
        max_attempts = 60
        for attempt in range(max_attempts):
            try:
                print(f"Attempt {attempt + 1}/{max_attempts}: Checking authentication status...")
                response = await self.app_context.one_dev_client.get_session(
                    headers={
                        "Content-Type": "application/json",
                        "X-Device-Code": device_code,
                    }
                )

                # Check if the auth token contains an error
                if 'error' not in response:
                    self.app_context.auth_token = response['jwt_token']
                    # Storing jwt token in user's machine using keyring
                    self.store_auth_token(self.app_context.auth_token)
                    print("Authentication successful!")
                    return self.app_context, ScreenType.DEFAULT  # Exit on success
                else:
                    print("Authentication is in progress. Please wait...")

            except Exception as e:
                print(f"Polling error: {e}")

            time.sleep(3)

        # If we reach here, it means authentication failed
        print("Authentication failed, please try again later.")

    async def login(self, auth_token: str) -> bool:
        """Attempts to authenticate the user using the provided auth token."""
        if not auth_token:
            print("Session not found in user's machine. Please login again!")
            return False

        try:
            print("Verifying the auth token...")
            response = await self.app_context.one_dev_client.verify_auth_token(
                    headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {auth_token}",
                        }
                )
            # Check if the response contains a status of 'verified'
            if response["status"] == "VERIFIED":
                print("Authenticated successfully!")
                return True
            else:
                print("Session is expired. Please login again!")
                return False

        except Exception as e:
            print(f"An error occurred during authentication: {e}. Please login again!")
            return False

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        print("Welcome to DeputyDev CLI!")
        print("Attempting to load your authentication token...")

        # Extracting auth token from user's machine
        auth_token = self.load_auth_token()
        if await self.login(auth_token):
            print("You are now logged in. Redirecting to the main interface...")
            return self.app_context, ScreenType.DEFAULT

        BASE_URL = 'http://localhost:3000'
        device_code = str(uuid.uuid4())
        is_cli = True

        auth_url = f"{BASE_URL}/cli?device_code={device_code}&is_cli={is_cli}"
        print(f"Please visit this link for authentication: {auth_url}")

        # Polling session
        return await self.poll_session(device_code)