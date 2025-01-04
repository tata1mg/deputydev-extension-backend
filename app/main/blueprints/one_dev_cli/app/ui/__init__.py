import asyncio
import sys
from typing import Dict, Optional

from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.one_dev_cli.app.clients.one_dev import OneDevClient
from app.main.blueprints.one_dev_cli.app.exceptions.exceptions import (
    InvalidVersionException,
)


async def close_session_and_exit(one_dev_client: OneDevClient):
    print("Exiting ...")
    await one_dev_client.close_session()
    sys.exit(0)


async def populate_config():
    one_dev_client = OneDevClient()

    # get the configs
    try:
        ConfigManager.initialize(in_memory=True)
        configs: Optional[Dict[str, str]] = await one_dev_client.get_configs(
            headers={"Content-Type": "application/json"}
        )
        if configs is None:
            raise Exception("No configs fetched")
        ConfigManager.set(configs)
    except InvalidVersionException:
        print("This CLI client is not supported anymore")
        await close_session_and_exit(one_dev_client)
    except Exception:
        print("Failed to fetch configs")
        await close_session_and_exit(one_dev_client)

    await one_dev_client.close_session()


asyncio.run(populate_config())
