import pytest
from playwright.sync_api import Page
import time
from random import randint
from instagram import login_to_instagram, get_value_from_cookies_by_key
from instagram import GRAPHQL_QUERY, get_following_count, get_follower_count, get_all_following, get_all_likers
from instagram import follow_unfollow_via_api
import requests


MAX_POTENCY_RATIO = 1
"""
potency_ratio with POSITIVE values can be used to route interactions to only potential (real) users WHOSE followers count is higher than following count (e.g., potency_ratio = 1.39) find desired potency_ratio with this formula: potency_ratio == followers count / following count (use desired counts)
potency_ratio with NEGATIVE values can be used to route interactions to only massive followers WHOSE following count is higher than followers count (e.g., potency_ratio = -1.42) find desired potency_ratio with this formula: potency_ratio == following count / followers count (use desired counts)
"""
SURREALDB_HEADERS = {
    'Accept': 'application/json, text/javascript, */*',
    'NS': 'myapplication',
    'DB': 'myapplication'    
}
"""
docker run --rm -p 8000:8000 surrealdb/surrealdb:latest start --log debug --user root --pass root memory
"""


@pytest.fixture()
def target_post_shortcode() -> int:
    return 22897081742


def test_main(page: Page, username: str, password: str, request_vars: dict, target_post_shortcode: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    # Unfollow all nonfollowers
    all_following = get_all_following(page, current_user_id)
    print(all_following)
    all_following['request_response'] = all_following.apply(
        lambda x: follow_unfollow_via_api(page, request_vars, x['id'], follow=False)['status'] if not x['follows_viewer'] else 'IS_FOLLOWER', axis=1
    )
    
    # Get all followers of target_post
    all_likers_of_target_post = get_all_likers(page, target_post_shortcode)
    print(all_likers_of_target_post)

    """
    Create function for determining whether or not to follow the target post's liker.
    If eligible, follow the liker and write a record to the database.
    """
    def follow_liker_and_write_record(liker_id: int, full_name: str, maximum_potency_ratio: float, is_private: bool, is_verified: bool) -> dict:
        following_count = get_following_count(page, liker_id)
        follower_count = get_follower_count(page, liker_id)

        if follower_count / following_count < maximum_potency_ratio & is_private:
            QUERY_TO_INSERT_FOLLOW_RECORD = f"""
            CREATE follow:{liker_id}
                SET time = time::now(),
                    full_name = '{full_name}',
                    follower_count = '{follower_count}',
                    following_count = '{following_count}',
                    is_private = {is_private},
                    is_verified = {is_verified};
            """
            response = requests.post('http://localhost:8000/sql', headers=SURREALDB_HEADERS, auth=('root', 'root'), data=QUERY_TO_INSERT_FOLLOW_RECORD).json()
            print(response)
            
            time.sleep(randint(5, 10))

            response = requests.post('http://localhost:8000/sql', headers=SURREALDB_HEADERS, auth=('root', 'root'), data='SELECT id FROM follow').json()
            if liker_id in [item['id'] for item in response['result'].items()]:
                print(f'{liker_id} (full_name={full_name}) was a previous follow.')
                return 'PREVIOUS_FOLLOW'
            else:
                print(f'{liker_id} (full_name={full_name}) is a new follow.')
                return follow_unfollow_via_api(page, request_vars, liker_id, follow=True)
    
    all_likers_of_target_post['request_response'] = all_likers_of_target_post.apply(
        lambda x: follow_liker_and_write_record(x['id'], x['full_name'], MAX_POTENCY_RATIO, x['is_private'], x['is_verified'])
    )

    print(all_likers_of_target_post)
