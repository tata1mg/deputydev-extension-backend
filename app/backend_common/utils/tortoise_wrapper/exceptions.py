"""Tortoise Wrapper Errors."""


class TortoiseWrapperError(Exception):
    """Base Tortoise Wrapper Exception."""


class ConfigError(TortoiseWrapperError):
    """Configurartion related errors."""


class BadRequestException(TortoiseWrapperError):
    """Runtime errors for Tortoise Wrapper"""
