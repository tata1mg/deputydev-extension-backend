from __future__ import annotations

from sanic.log import logger
from tortoise import Tortoise

from app.backend_common.utils.tortoise_wrapper.config import PostgresConfig
from app.backend_common.utils.tortoise_wrapper.constants import ASYNCPG_ENGINE
from app.backend_common.utils.tortoise_wrapper.exceptions import ConfigError


class TortoiseWrapper:
    @classmethod
    async def setup(
        cls,
        *,
        config: dict | PostgresConfig,
        replica_config: dict | PostgresConfig | None = None,
        orm_config: dict | None = None,
        generate_schemas: bool = False,
    ) -> None:
        """
        Initialize the Tortoise ORM with the given configuration.

        Args:
            config (dict | PostgresConfig): Primary database configuration.
            replica_config (dict | PostgresConfig | None): Replica database configuration, if any. Defaults to None.
            orm_config (dict | None): Direct ORM configuration. If provided, it takes precedence over the generated configuration. Defaults to None.
            generate_schemas (bool): Whether to generate database schemas. Defaults to False.

        Returns:
            None
        """  # noqa: E501
        if orm_config:
            await Tortoise.init(config=orm_config)

        else:
            _name = config.NAME if isinstance(config, PostgresConfig) else config.get("NAME")
            orm_config = {
                "apps": {
                    _name: {
                        "models": ["app.models", "app.signals"],
                        "default_connection": "default",
                    }
                },
            }

            connections = {}
            connections["default"] = cls.__get_connection_config(config)
            if replica_config:
                connections["replica"] = cls.__get_connection_config(replica_config)
            orm_config["connections"] = connections
            await Tortoise.init(config=orm_config)

        if generate_schemas:
            logger.info("Tortoise-ORM generating schema")
            await Tortoise.generate_schemas()

    @classmethod
    async def teardown(cls) -> None:
        """Close all database connections."""
        await Tortoise.close_connections()

    @staticmethod
    def __get_connection_config(config: dict | PostgresConfig) -> dict:
        """
        Generate a Tortoise ORM connection configuration from the given config.

        Args:
            config (dict | PostgresConfig): The database configuration.

        Returns:
            dict: The connection configuration.

        Raises:
            ConfigError: If the provided config is not of the correct type.
        """
        if isinstance(config, dict):
            config = PostgresConfig.from_dict(config)

        if not isinstance(config, PostgresConfig):
            raise ConfigError(f"Invalid config type: {type(config)}")

        return {
            "engine": ASYNCPG_ENGINE,
            "credentials": {
                "host": config.POSTGRES_HOST,
                "port": config.POSTGRES_PORT,
                "user": config.POSTGRES_USER,
                "password": config.POSTGRES_PASS,
                "database": config.POSTGRES_DB,
                "minsize": config.POSTGRES_POOL_MIN_SIZE,
                "maxsize": config.POSTGRES_POOL_MAX_SIZE,
            },
        }
