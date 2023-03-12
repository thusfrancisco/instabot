from src.supabase import new_client, n_days_ago_datetime_as_str
import time


SURREALDB_HEADERS = {
    'Accept': 'application/json',
    'NS': 'myapplication',
    'DB': 'myapplication'    
}

QUERY_TO_INSERT_FOLLOW_RECORD = f"""
CREATE follow:123
    SET time = time::now(),
        full_name = '123',
        follower_count = '123',
        following_count = '123',
        is_private = true,
        is_verified = true;
"""

QUERY_TO_INSERT_FOLLOW_RECORD = f"""
SELECT id FROM follow
"""

# print(requests.post('http://localhost:8000/sql', headers=SURREALDB_HEADERS, auth=('root', 'root'), data=QUERY_TO_INSERT_FOLLOW_RECORD).json())
"""
docker run --rm -p 8000:8000 surrealdb/surrealdb:latest start --log debug --user root --pass root memory
"""
"""
docker run --name instagres -e POSTGRES_PASSWORD=XkPgRFJdo4A2rK5Y -e POSTGRES_USER=sa -p 5432:5432 -v /data:/var/lib/postgresql/data postgres
docker run --name pgadmin -p 8000:8000 -e 'PGADMIN_DEFAULT_EMAIL=franciscoabsampaio@protonmail.com' -e 'PGADMIN_DEFAULT_PASSWORD=rr3FJso6XFgzQdNcxjKi'-d dpage/pgadmin4
"""


def test_connect():
    supabase = new_client()

    assert supabase


def test_select_all_previous_follows():
    supabase = new_client()
    
    assert "data" in supabase.table("follows").select("*").execute().json()


def test_insert_into_follows_record_with_time():
    supabase = new_client()
    response = supabase.table("follows").insert({
        'id': 0,
        'created_at': time.time(),
        'full_name': 'John Smith',
        'follower_count': 0,
        'following_count': 0,
        'is_private': True,
        'is_verified': False
    }).execute()

    assert "data" in response.json()

    supabase.table("follows").delete().eq("id", 0).execute()


def test_insert_into_follows_record_without_time():
    supabase = new_client()
    response = supabase.table("follows").insert({
        'id': 0,
        'full_name': 'John Smith',
        'follower_count': 0,
        'following_count': 0,
        'is_private': True,
        'is_verified': False
    }).execute()

    assert "data" in response.json()

    supabase.table("follows").delete().eq("id", 0).execute()


def test_insert_into_follows_record_without_fullname():
    supabase = new_client()
    response = supabase.table("follows").insert({
        'id': 0,
        'full_name': None,
        'follower_count': 0,
        'following_count': 0,
        'is_private': True,
        'is_verified': False
    }).execute()

    assert "data" in response.json()

    supabase.table("follows").delete().eq("id", 0).execute()


def test_select_follows_older_than():
    supabase = new_client()

    response = supabase.table('follows').select('id', 'created_at').lte('created_at', n_days_ago_datetime_as_str(n_days=7)).execute()
    
    assert "data" in response.json()
