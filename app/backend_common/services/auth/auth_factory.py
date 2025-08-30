from typing import Dict, Type

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.services.auth.base_auth import BaseAuth
from app.backend_common.services.auth.fake_auth.fake_auth import FakeAuth
from app.backend_common.services.auth.supabase.supabase_auth import SupabaseAuth
from app.backend_common.utils.dataclasses.main import AuthProvider


class AuthFactory:
    """
    A factory class that provides authentication provider instances.

    This factory is responsible for creating and returning the appropriate authentication
    provider instance based on the application's configuration and requested provider type.
    It supports multiple authentication providers and can be easily extended to support more.
    """

    @staticmethod
    def get_auth_provider(auth_provider: AuthProvider = AuthProvider.SUPABASE) -> BaseAuth:
        """
        Get an instance of the requested authentication provider.

        Args:
            auth_provider (AuthProvider, optional): The type of authentication provider to create.
                Defaults to AuthProvider.SUPABASE.

        Returns:
            BaseAuth: An instance of the requested authentication provider.

        Raises:
            ValueError: If the specified provider is not supported.

        Note:
            If FAKE_AUTH is enabled in the configuration, this method will always return
            a FakeAuth instance regardless of the requested provider.
        """
        auth_providers: Dict[AuthProvider, Type[BaseAuth]] = {
            AuthProvider.SUPABASE: SupabaseAuth,
            AuthProvider.FAKEAUTH: FakeAuth,
        }
        if ConfigManager.configs["FAKE_AUTH"] and ConfigManager.configs["FAKE_AUTH"]["ENABLED"]:
            return FakeAuth()

        if auth_provider not in auth_providers:
            raise ValueError(f"Invalid provider: {auth_provider}")
        return auth_providers[auth_provider]()
