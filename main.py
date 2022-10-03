import time
import re
from playwright.sync_api import Page, expect
import pytest
import os


@pytest.fixture()
def username() -> str:
    return os.environ.get("INSTA_USERNAME")


@pytest.fixture()
def password() -> str:
    return os.environ.get("INSTA_PASSWORD")


def test_goto_instagram_homepage_and_check_title(page: Page):
    page.goto("https://www.instagram.com/")

    expect(page).to_have_title(re.compile("Instagram"))
    

def test_username_and_password_are_strings(username, password):
    assert isinstance(username, str)
    assert isinstance(password, str)


def test_goto_instagram_page_and_login(page: Page, username, password):
    page.goto("https://www.instagram.com/")

    button_only_allow_essential_cookies = page.locator('button:text("Only allow essential cookies")')
    button_only_allow_essential_cookies.click()

    input_username = page.locator('input[name="username"]')
    input_username.type(username, delay=100)

    input_password = page.type('input[name="password"]', password, delay=100)

    button_log_in = page.locator('button>div:text("Log in")')
    button_log_in.click()

    button_dont_save_loggin_info = page.locator('button:text("Not Now")')
    button_dont_save_loggin_info.click()

    button_dont_turn_on_notifications = page.locator('button:text("Not Now")')
    button_dont_turn_on_notifications.click()
    
    time.sleep(30)
