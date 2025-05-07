import time
import uuid
from typing import Optional

from deputydev_core.services.auth_token_storage.cli_auth_token_storage_manager import (
    CLIAuthTokenStorageManager,
)
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.constants.auth import AuthStatus
from deputydev_core.utils.constants.enums import ContextValueKeys
from deputydev_core.utils.context_value import ContextValue
from deputydev_core.utils.exceptions import InvalidVersionException
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.validation import ValidationError

from app.main.blueprints.deputydev_cli.app.clients.browser import BrowserClient
from app.main.blueprints.deputydev_cli.app.clients.one_dev_cli_client import (
    OneDevCliClient,
)


class AuthenticationManager:
    def __init__(self, one_dev_client: OneDevCliClient, prompt_session: PromptSession[str]) -> None:
        self.session = prompt_session
        self.one_dev_client = one_dev_client

    async def poll_session_and_get_auth_token(self, supabase_session_id: str) -> str:
        """Polls the session for authentication status."""

        print_formatted_text("Authentication is in progress. Please wait...")
        max_attempts = 60
        for _attempt in range(max_attempts):
            try:
                response = await self.one_dev_client.get_session(
                    headers={
                        "Content-Type": "application/json",
                        "X-Supabase-Session-Id": supabase_session_id,
                    }
                )
                print(response)

                if response.get("status") == AuthStatus.AUTHENTICATED.value:
                    if not response.get("encrypted_session_data") or response.get("encrypted_session_data") is None:
                        raise Exception("No encrypted session data found in response")
                    # Storing jwt token in user's machine using keyring
                    CLIAuthTokenStorageManager.store_auth_token(response["encrypted_session_data"])
                    ContextValue.get(ContextValueKeys.CLI_AUTH_TOKEN.value, response["encrypted_session_data"])
                    return response["encrypted_session_data"]  # Exit on success
                time.sleep(3)  # Wait for 3 seconds before polling again
            except Exception as e:
                AppLogger.log_debug(f"Error polling session: {e}")
                time.sleep(1)  # Wait for 1 second on exception

        # If we reach here, it means authentication failed
        print_formatted_text("Authentication failed, please try again later.")
        raise Exception("Authentication failed, please try again later.")

    async def get_current_session_auth_token(self) -> Optional[str]:
        """Attempts to authenticate the user using the provided auth token."""

        # Extracting auth token from user's machine
        auth_token = CLIAuthTokenStorageManager.load_auth_token()

        if not auth_token:
            return None

        try:
            response = await self.one_dev_client.verify_auth_token(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {auth_token}",
                }
            )
            # Check if the response contains a status of 'verified'
            if response["status"] == AuthStatus.VERIFIED.value:
                return CLIAuthTokenStorageManager.load_auth_token()
            elif response["status"] == AuthStatus.EXPIRED.value:
                if not response.get("encrypted_session_data") or response.get("encrypted_session_data") is None:
                    raise Exception("No encrypted session data found in response")
                CLIAuthTokenStorageManager.store_auth_token(response["encrypted_session_data"])
                ContextValue.get(ContextValueKeys.CLI_AUTH_TOKEN.value, response["encrypted_session_data"])
                return CLIAuthTokenStorageManager.load_auth_token()
            else:
                return None

        except InvalidVersionException as ex:
            raise ValidationError(message=str(ex))
        except Exception:
            print_formatted_text("Authentication failed, please try again later.")
            return None

    async def authenticate_and_get_auth_token(self) -> str:
        # Check if the current session is present and valid
        auth_token = await self.get_current_session_auth_token()

        if auth_token:
            return auth_token

        # If the current session is not present or is not valid, initiate login
        supabase_session_id = str(uuid.uuid4())
        BrowserClient.initiate_cli_login(supabase_session_id)

        # Polling session
        return await self.poll_session_and_get_auth_token(supabase_session_id)
