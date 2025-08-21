import asyncio

from deputydev_core.utils.config_manager import ConfigManager

ConfigManager.initialize()

from app.main.blueprints.one_dev.services.migration.migration_manager import MessageThreadMigrationManager  # noqa: E402

if __name__ == "__main__":
    asyncio.run(MessageThreadMigrationManager.migrate_to_agent_chats())
