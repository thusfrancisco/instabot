from playwright.sync_api import Page, expect
import re
import pandas as pd
from src.instagram import login_to_instagram, create_conversation_via_ui, follow_unfollow_via_ui, paste_from_clipboard_to_textarea_via_ui, send_message_via_ui, write_message_to_textarea_via_ui
from src.instagram import get_value_from_cookies_by_key, get_all_cookies
from src.instagram import GRAPHQL_QUERY, query_graphql_next_page, get_following_count, get_follower_count, get_all_following, get_all_followers
from src.instagram import follow_unfollow_via_api, create_conversation_via_api
import time


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
    
    assert follow_unfollow_via_api(page, request_vars, 232192182, follow=False)['status_code'] == 200
 

def test_create_conversation_via_api(page: Page, username: str, password: str, request_vars: dict):
    """
    NOT WORKING!
    """
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    page.goto("https://www.instagram.com/direct/inbox/")
    
    assert isinstance(create_conversation_via_api(page, request_vars, ['50791316724']), int)  # TODO: change to NOT true
    time.sleep(10)
    assert True


def test_create_conversation_via_ui(page: Page, username: str, password: str):
    """
    If there's at least 2 counts of the profile picture, and the recipient is not the same as the sender,
    then if the page is https://www.instagram.com/direct/inbox/ a conversation with the recipient must exist and be open.
    """
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    page.goto("https://www.instagram.com/direct/inbox/")

    recipient_username = 'anna_2lucy'

    page = create_conversation_via_ui(page, recipient_username)

    expect(page.locator(f'img[alt="{recipient_username}\'s profile picture"]')).to_have_count(2)


def test_follow_via_ui(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)

    assert follow_unfollow_via_ui(page, target_username='therock', follow=True) == 'therock'


def test_unfollow_via_ui(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)

    assert follow_unfollow_via_ui(page, target_username='therock', follow=False) == 'therock'


def test_paste_from_clipboard_and_send_message_via_ui(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    page.goto("https://www.instagram.com/direct/inbox/")

    recipient_username = 'luis03sampaio'

    page = create_conversation_via_ui(page, recipient_username)

    page = paste_from_clipboard_to_textarea_via_ui(page)

    page = send_message_via_ui(page)


def test_write_message_and_send_message_via_ui(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    page.goto("https://www.instagram.com/direct/inbox/")

    recipient_username = 'luis03sampaio'

    page = create_conversation_via_ui(page, recipient_username)

    page = write_message_to_textarea_via_ui(page, message_to_send="Hello, world!")

    page = send_message_via_ui(page)

