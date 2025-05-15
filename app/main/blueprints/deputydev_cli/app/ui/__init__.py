import asyncio
import sys
from typing import Dict, Optional

from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.exceptions import InvalidVersionException
from prompt_toolkit import PromptSession

from app.main.blueprints.deputydev_cli.app.clients.one_dev_cli_client import (
    OneDevCliClient,
)

one_dev_client = OneDevCliClient()

auth_token: Optional[str] = None


async def close_session_and_exit():
    print("Exiting ...")
    global one_dev_client
    await one_dev_client.close_session()
    sys.exit(0)


async def populate_essential_config():
    # get the configs
    global one_dev_client
    try:
        ConfigManager.initialize(in_memory=True)
        configs: Optional[Dict[str, str]] = await one_dev_client.get_essential_configs(
            headers={"Content-Type": "application/json"}
        )
        if configs is None:
            raise Exception("No configs fetched")
        ConfigManager.set(configs)
    except InvalidVersionException:
        print("This CLI client is not supported anymore")
        await close_session_and_exit()
    except Exception:
        print("Failed to fetch configs")
        await close_session_and_exit()


async def populate_full_config():
    # get the configs
    global one_dev_client
    global auth_token
    try:
        configs: Optional[Dict[str, str]] = await one_dev_client.get_configs(
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {auth_token}"}
        )
        if configs is None:
            raise Exception("No configs fetched")
        ConfigManager.set(configs)
    except Exception:
        print("Failed to fetch configs")
        await close_session_and_exit()


async def initialize_cli_ui():
    # get the essential configs
    await populate_essential_config()

    # authenticate the user
    global auth_token
    global one_dev_client

    try:
        from app.main.blueprints.deputydev_cli.app.managers.authentication.authentication_manager import (
            AuthenticationManager,
        )

        prompt_session: PromptSession[str] = PromptSession()
        authentication_manager = AuthenticationManager(one_dev_client, prompt_session)
        auth_token = await authentication_manager.authenticate_and_get_auth_token()
        print(auth_token)
    except Exception:
        print("Failed to authenticate user")
        await close_session_and_exit()

    # update the configs
    await populate_full_config()
    await one_dev_client.close_session()


asyncio.run(initialize_cli_ui())
