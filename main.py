import pytest
import os
from playwright.sync_api import Page, expect
import re
import time
from instagram import login_to_instagram, get_value_from_cookies_by_key, get_following_users_next_page


@pytest.fixture(autouse=True)
def sleep_between_tests():
    yield
    time.sleep(30)


@pytest.fixture()
def username() -> str:
    return os.environ.get("INSTA_USERNAME")


@pytest.fixture()
def password() -> str:
    return os.environ.get("INSTA_PASSWORD")


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


def test_get_first_page_of_following_users(page: Page, username: str, password: str):
    page.goto("https://www.instagram.com/")

    page = login_to_instagram(page, username, password)
    
    current_user_id = get_value_from_cookies_by_key(page, key='ds_user_id')

    first_page_of_following_users = get_following_users_next_page(page, current_user_id, first=1)

    following_count = first_page_of_following_users['data']['user']['edge_follow']['count']
    assert following_count >= 0
    
    # If more than one user is being followed, there must be a second page, thus has_next_page must be True
    if following_count > 1:
        assert first_page_of_following_users['data']['user']['edge_follow']['page_info']['has_next_page']
