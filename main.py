import pytest
import os
from playwright.sync_api import Page, expect
import re
import time
import pandas as pd
from instagram import login_to_instagram, get_value_from_cookies_by_key, get_all_cookies
from instagram import GRAPHQL_QUERY, query_graphql_next_page, get_following_count, get_follower_count, get_all_following, get_all_followers
from instagram import follow_unfollow_via_api


@pytest.fixture(autouse=True)
def sleep_between_tests():
    yield
    time.sleep(20)


@pytest.fixture()
def username() -> str:
    return os.environ.get("INSTA_USERNAME")


@pytest.fixture()
def password() -> str:
    return os.environ.get("INSTA_PASSWORD")


@pytest.fixture()
def request_vars() -> str:
    return {
        'x-asbd-id': os.environ.get("x-asbd-id"),
        'x-ig-app-id': os.environ.get("x-ig-app-id"),
        'x-ig-www-claim': os.environ.get("x-ig-www-claim"),
        'x-instagram-ajax': os.environ.get("x-instagram-ajax")
    }


def test_goto_instagram_homepage_and_check_title(page: Page):
    page.goto("https://www.instagram.com/")

    expect(page).to_have_title(re.compile("Instagram"))
    

def test_username_and_password_are_strings(username: str, password: str):
    assert isinstance(username, str)
    assert isinstance(password, str)


def test_goto_instagram_page_and_login(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    expect(page.locator(f'div>a:text("{username}")')).to_be_visible()


def test_get_current_user_id(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    assert current_user_id.isnumeric()


def test_get_all_cookies(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)

    cookies_dict = get_all_cookies(page)
    
    assert isinstance(cookies_dict, dict)
    assert cookies_dict.get("ds_user_id")
    

def test_query_graphql_next_page(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    first_page_of_following_users = query_graphql_next_page(GRAPHQL_QUERY['following'], page, current_user_id, first=1)

    following_count = first_page_of_following_users['data']['user']['edge_follow']['count']
    assert following_count >= 0
    
    # If more than one user is being followed, there must be a second page, thus has_next_page must be True
    if following_count > 1:
        assert first_page_of_following_users['data']['user']['edge_follow']['page_info']['has_next_page']


def test_get_following_count(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    assert isinstance(get_following_count(page, current_user_id), int)


def test_get_follower_count(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    assert isinstance(get_follower_count(page, current_user_id), int)


def test_get_all_following(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    all_following_users = get_all_following(page, current_user_id)

    assert isinstance(all_following_users, pd.DataFrame)
    assert all_following_users.columns.to_list() == [
        'id',
        'username',
        'full_name',
        'profile_pic_url',
        'is_private',
        'is_verified',
        'followed_by_viewer',
        'follows_viewer',
        'requested_by_viewer'
    ]


def test_get_all_followers(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    all_following_users = get_all_followers(page, current_user_id)

    assert isinstance(all_following_users, pd.DataFrame)
    assert all_following_users.columns.to_list() == [
        'id',
        'username',
        'full_name',
        'profile_pic_url',
        'is_private',
        'is_verified',
        'followed_by_viewer',
        'follows_viewer',
        'requested_by_viewer'
    ]


def test_follow_user_via_api(page: Page, username: str, password: str, request_vars: dict):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    assert follow_unfollow_via_api(page, request_vars, 232192182)['result'] == 'following'


def test_unfollow_user_via_api(page: Page, username: str, password: str, request_vars: dict):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    assert follow_unfollow_via_api(page, request_vars, 232192182, follow=False)['status'] == 'ok'
 