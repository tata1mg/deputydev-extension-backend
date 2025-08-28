from typing import Dict, Type

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.services.auth.base_auth import BaseAuth
from app.backend_common.services.auth.fake_auth.fake_auth import FakeAuth
from app.backend_common.services.auth.supabase.supabase_auth import SupabaseAuth
from app.backend_common.utils.dataclasses.main import AuthProvider


class AuthFactory:
    @staticmethod
    def get_auth_provider(auth_provider: AuthProvider = AuthProvider.SUPABASE) -> BaseAuth:
        auth_providers: Dict[AuthProvider, Type[BaseAuth]] = {
            AuthProvider.SUPABASE: SupabaseAuth,
            AuthProvider.FAKEAUTH: FakeAuth,
        }
        if ConfigManager.configs["FAKE_AUTH"] and ConfigManager.configs["FAKE_AUTH"]["ENABLED"]:
            return FakeAuth()

        if auth_provider not in auth_providers:
            raise ValueError(f"Invalid provider: {auth_provider}")
        return auth_providers[auth_provider]()
