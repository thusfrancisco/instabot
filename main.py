import pytest
from playwright.sync_api import Page
import time
from random import randint
from src.instagram import login_to_instagram, get_value_from_cookies_by_key
from src.instagram import GRAPHQL_QUERY, get_following_count, get_follower_count, get_all_following, get_all_likers
from src.instagram import follow_unfollow_via_api
import pandas as pd
import os
from src.supabase import new_client


MAX_POTENCY_RATIO = 1
"""
potency_ratio with POSITIVE values can be used to route interactions to only potential (real) users WHOSE followers count is higher than following count (e.g., potency_ratio = 1.39) find desired potency_ratio with this formula: potency_ratio == followers count / following count (use desired counts)
potency_ratio with NEGATIVE values can be used to route interactions to only massive followers WHOSE following count is higher than followers count (e.g., potency_ratio = -1.42) find desired potency_ratio with this formula: potency_ratio == following count / followers count (use desired counts)
"""
"""
docker run --rm -p 8000:8000 surrealdb/surrealdb:latest start --log debug --user root --pass root memory
"""
"""
docker run --name instagres -e POSTGRES_PASSWORD=XkPgRFJdo4A2rK5Y -e POSTGRES_USER=sa -p 5432:5432 -v /data:/var/lib/postgresql/data postgres
docker run --name pgadmin -p 8000:8000 -e 'PGADMIN_DEFAULT_EMAIL=franciscoabsampaio@protonmail.com' -e 'PGADMIN_DEFAULT_PASSWORD=rr3FJso6XFgzQdNcxjKi'-d dpage/pgadmin4
"""


@pytest.fixture()
def target_post_shortcode() -> str:
    return 'CjqvpJSNy9x'


@pytest.fixture()
def supabase_api_key() -> str:
    return os.environ.get("SUPABASE_API_KEY")


@pytest.fixture()
def session(page: Page, username: str, password: str) -> Page:
    page.goto("https://www.instagram.com/")

    return login_to_instagram(page, username, password)


def test_unfollow_nonfollowers(session: Page, request_vars: dict):
    
    current_user_id = get_value_from_cookies_by_key(session, key='ds_user_id')

    # Unfollow all nonfollowers
    if os.path.isfile('following.csv'):
        all_following = pd.read_csv('following.csv')
    else:
        all_following = get_all_following(session, current_user_id)
        print('Saving all following to csv...')
        all_following.to_csv('following.csv', index=False)
    
    all_following['request_response'] = all_following.apply(
        lambda x: follow_unfollow_via_api(session, request_vars, x['id'], follow=False)['status'] if not x['follows_viewer'] else 'IS_FOLLOWER', axis=1
    )
    all_following.to_csv('following.csv', index=False)


def test_follow_likers(session: Page, request_vars: dict, target_post_shortcode: str):
    
    current_user_id = get_value_from_cookies_by_key(session, key='ds_user_id')

    likers_filename = f'likers_{target_post_shortcode}.csv'

    # Get all followers of target_post
    if os.path.isfile(likers_filename):
        all_likers_of_target_post = pd.read_csv(likers_filename)
    else:
        all_likers_of_target_post = get_all_likers(session, target_post_shortcode)
        print('Saving all likers to csv...')
        all_likers_of_target_post.to_csv(likers_filename, index=False)

    """
    Create function for determining whether or not to follow the target post's liker.
    If eligible, follow the liker and write a record to the database.
    """
    def follow_liker_and_write_record(liker_id: int, full_name: str, maximum_potency_ratio: float, is_private: bool, is_verified: bool) -> dict:
        following_count = get_following_count(session, liker_id)
                
        time.sleep(randint(3, 8))

        follower_count = get_follower_count(session, liker_id)
                
        time.sleep(randint(3, 8))

        if follower_count / following_count < maximum_potency_ratio & is_private:
            supabase = new_client()
            previous_follows = supabase.table("follows").select("id").execute().data

            if liker_id in pd.DataFrame(previous_follows).values:
                print(f'{liker_id} (full_name={full_name}) was a previous follow.')
                return 'PREVIOUS_FOLLOW'
            else:
                print(f'{liker_id} (full_name={full_name}) is a new follow.')
                
                response = supabase.table("follows").insert({
                    'id': liker_id,
                    'full_name': full_name,
                    'follower_count': follower_count,
                    'following_count': following_count,
                    'is_private': is_private,
                    'is_verified': is_verified
                }).execute()

                return follow_unfollow_via_api(session, request_vars, liker_id, follow=True)

    all_likers_of_target_post['request_response'] = all_likers_of_target_post.apply(
        lambda x: follow_liker_and_write_record(
            x['id'], x['full_name'], MAX_POTENCY_RATIO, x['is_private'], x['is_verified']
        ) if not x['followed_by_viewer'] else 'ALREADY_FOLLOWED',
        axis=1
    )

    all_likers_of_target_post.to_csv(likers_filename, index=False)
