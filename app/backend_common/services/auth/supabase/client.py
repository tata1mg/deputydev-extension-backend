from torpedo import CONFIG

from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

class SupabaseClient:
    _instance: Client = None
    supabase = CONFIG.config["SUPABASE"]

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = create_client(cls.supabase["URL"], cls.supabase["KEY"], options=SyncClientOptions(auto_refresh_token=False))
        return cls._instance
