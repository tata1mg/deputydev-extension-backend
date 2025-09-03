"""Dataclasses for structured configurations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HostConfig:
    """Configuration for the host.

    Attributes:
        NAME (str): The name of the host.
        HOST (str): The host address.
        PORT (str): The port number.
        WORKERS (int): The number of worker processes.
        SINGLE_PROCESS (bool): Whether to run in single process mode.
        DEBUG (bool): Whether to run in debug mode.
        ACCESS_LOG (bool): Whether to enable access logging.
    """

    NAME: str
    HOST: str
    PORT: str
    WORKERS: int = 1
    SINGLE_PROCESS: bool = True
    DEBUG: bool = False
    ACCESS_LOG: bool = True
    DEV_MODE: bool = True

    @classmethod
    def from_dict(cls, config: dict) -> HostConfig:
        return cls(
            NAME=config["NAME"],
            HOST=config["HOST"],
            PORT=config["PORT"],
            WORKERS=config.get("WORKERS", 1),
            SINGLE_PROCESS=config.get("SINGLE_PROCESS", True),
            DEBUG=config.get("DEBUG", False),
            ACCESS_LOG=config.get("ACCESS_LOG", True),
            DEV_MODE=config.get("DEV_MODE", True),
        )


@dataclass
class SentryConfig:
    """
    Configuration for Sentry integration.

    Attributes:
        DSN (str): The Sentry DSN.
        ENVIRONMENT (str): The environment name.
        SERVICE_NAME (str): The name of the service.
        RELEASE_TAG (str): The release tag.
    """

    DSN: str
    ENVIRONMENT: str
    SERVICE_NAME: str
    RELEASE_TAG: str
    CAPTURE_WARNING: bool = False
