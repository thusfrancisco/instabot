from supabase import create_client, Client
import os
from datetime import datetime, timezone, timedelta


def new_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)


def n_days_ago_datetime_as_str(n_days: int = 7) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n_days)).astimezone().strftime("%Y-%m-%d %H:%M:%S.%f%z")[:-2]
