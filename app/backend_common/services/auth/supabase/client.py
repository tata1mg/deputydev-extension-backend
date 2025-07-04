from typing import TYPE_CHECKING

from torpedo import CONFIG

from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

if TYPE_CHECKING:
    from supabase._sync.client import SyncClient


class SupabaseClient:
    _instance: Client = None
    supabase = CONFIG.config["SUPABASE"]

    @classmethod
    def get_instance(cls) -> "SyncClient":
        if cls._instance is None:
            cls._instance = create_client(
                cls.supabase["URL"], cls.supabase["KEY"], options=SyncClientOptions(auto_refresh_token=False)
            )
        return cls._instance
