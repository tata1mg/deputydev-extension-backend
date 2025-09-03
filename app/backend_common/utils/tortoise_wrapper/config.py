from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PostgresConfig:
    NAME: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASS: str
    POSTGRES_DB: str
    POSTGRES_POOL_MIN_SIZE: int = 1
    POSTGRES_POOL_MAX_SIZE: int = 5

    @classmethod
    def from_dict(cls, config: dict) -> PostgresConfig:
        return cls(
            NAME=config["NAME"],
            POSTGRES_HOST=config["POSTGRES_HOST"],
            POSTGRES_PORT=config["POSTGRES_PORT"],
            POSTGRES_USER=config["POSTGRES_USER"],
            POSTGRES_PASS=config["POSTGRES_PASS"],
            POSTGRES_DB=config["POSTGRES_DB"],
            POSTGRES_POOL_MIN_SIZE=config.get("POSTGRES_POOL_MIN_SIZE", 1),
            POSTGRES_POOL_MAX_SIZE=config.get("POSTGRES_POOL_MAX_SIZE", 5),
        )
