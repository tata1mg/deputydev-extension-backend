from torpedo import CONFIG
from supabase import create_client, Client

supabase_url = CONFIG.config["SUPABASE"]["SUPABASE_URL"]
supabase_key = CONFIG.config["SUPABASE"]["SUPABASE_KEY"]

url: str = supabase_url
key: str = supabase_key
supabase: Client = create_client(url, key)
