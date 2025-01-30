import asyncio
import sys
from typing import Dict, Optional

from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputydev_cli.app.clients.one_dev import OneDevClient
from app.main.blueprints.deputydev_cli.app.exceptions.exceptions import (
    InvalidVersionException,
)

from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import AppContext, ScreenType


one_dev_client = OneDevClient()
app_context = AppContext(one_dev_client=one_dev_client)


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
    except Exception:
        print("Failed to fetch configs")


async def populate_full_config():
    # get the configs
    global one_dev_client
    global app_context
    try:
        configs: Optional[Dict[str, str]] = await one_dev_client.get_configs(
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {app_context.auth_token}"}
        )
        if configs is None:
            raise Exception("No configs fetched")
        ConfigManager.set(configs)
    except Exception:
        print("Failed to fetch configs")


async def initialize_cli_ui():
    # get the essential configs
    await populate_essential_config()

    # authenticate the user
    global app_context
    global one_dev_client
    from app.main.blueprints.deputydev_cli.app.ui.screens.authentication import (
        Authentication,
    )
    updated_app_context, redirect_screen = await Authentication(app_context).render()

    if redirect_screen == ScreenType.EXIT or redirect_screen == ScreenType.HOME:
        await close_session_and_exit()

    app_context = updated_app_context

    # update the configs
    await populate_full_config()
    await one_dev_client.close_session()


asyncio.run(initialize_cli_ui())
