from playwright.sync_api import sync_playwright, Page
import pytest
import os
import time


@pytest.fixture(autouse=False)
def sleep_between_tests():
    yield
    time.sleep(20)


@pytest.fixture(scope="session")
def username() -> str:
    return os.environ.get("INSTA_USERNAME")


@pytest.fixture(scope="session")
def password() -> str:
    return os.environ.get("INSTA_PASSWORD")

    
@pytest.fixture()
def target_post_shortcode() -> str:
    return os.environ.get('TARGET_POST_ID')


@pytest.fixture()
def cdp_port() -> str:
    return os.environ.get('CDP_PORT')


@pytest.fixture()
def flag_use_cdp_target() -> bool:
    return os.environ.get('FLAG_USE_CDP_TARGET') == 'True'
    

@pytest.fixture()
def flag_is_already_logged_in() -> bool:
    return os.environ.get('FLAG_IS_ALREADY_LOGGED_IN') == 'True'


@pytest.fixture()
def context_and_page(flag_use_cdp_target: bool, cdp_port: str) -> Page:
    with sync_playwright() as playwright:
        if flag_use_cdp_target:
            print(f"Connecting to existing browser via port {cdp_port}")

            browser = playwright.chromium.connect_over_cdp(f"http://localhost:{cdp_port}")
            existing_context = browser.contexts[0]
            
            print(f"Current pages open:")
            print(existing_context.pages)

            """
            The real problem is when the page URL is "https://gx-corner.opera.com/".
            Instead, just use the currently open page.
            
            (Deprecated) Workaround for the following error:

            E       playwright._impl._api_types.Error: net::ERR_ABORTED at https://www.instagram.com/
            E       =========================== logs ===========================
            E       navigating to "https://www.instagram.com/", waiting until "load"
            E       ============================================================

            References:
            https://github.com/microsoft/playwright/issues/13640
            https://github.com/microsoft/playwright/issues/2061#issuecomment-623100345
            
            time.sleep(1)
            """
            i = 0
            while existing_context.pages[i].url != "https://www.instagram.com/":
                i += 1
            page = existing_context.pages[i]

            """
            Yield is required even if no cleanup is needed, because otherwise the tests will exit the sync_playwright() context and the fixture will immediately return None.
            """
            yield page  
        else:
            print(f"Launching new incognito browser instance")

            browser = playwright.chromium.launch()

            page = browser.new_page()
            
            yield page
            browser.close()


@pytest.fixture()
def request_vars() -> str:
    return {
        'x-asbd-id': os.environ.get("x-asbd-id"),
        'x-ig-app-id': os.environ.get("x-ig-app-id"),
        'x-ig-www-claim': os.environ.get("x-ig-www-claim"),
        'x-instagram-ajax': os.environ.get("x-instagram-ajax")
    }
