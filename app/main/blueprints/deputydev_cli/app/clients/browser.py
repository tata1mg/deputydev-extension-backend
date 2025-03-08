import webbrowser

from deputydev_core.utils.config_manager import ConfigManager
from prompt_toolkit import print_formatted_text


class BrowserClient:
    @classmethod
    def initiate_cli_login(cls, supabase_session_id: str):
        is_external_auth_request = "true"

        auth_url = f"{ConfigManager.configs['DD_BROWSER_HOST']}/external-auth?supabase_session_id={supabase_session_id}&is_external_auth_request={is_external_auth_request}"
        print_formatted_text(f"Please visit this link for authentication: {auth_url}")

        # Open the URL in the default web browser
        webbrowser.open(auth_url)
