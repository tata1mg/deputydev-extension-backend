from supabase import Client, create_client
from torpedo import CONFIG


class SupabaseClient:
    _instance: Client = None
    supabase = CONFIG.config["SUPABASE"]

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = create_client(cls.supabase["URL"], cls.supabase["KEY"])
        return cls._instance
