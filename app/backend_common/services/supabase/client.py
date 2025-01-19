from supabase import Client, create_client
from torpedo import CONFIG

supabase_url = CONFIG.config["SUPABASE"]["SUPABASE_URL"]
supabase_key = CONFIG.config["SUPABASE"]["SUPABASE_KEY"]

url: str = supabase_url
key: str = supabase_key
supabase: Client = create_client(url, key)
