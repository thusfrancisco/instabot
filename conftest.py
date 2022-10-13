import pytest
import os
import time


@pytest.fixture(autouse=True)
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
def request_vars() -> str:
    return {
        'x-asbd-id': os.environ.get("x-asbd-id"),
        'x-ig-app-id': os.environ.get("x-ig-app-id"),
        'x-ig-www-claim': os.environ.get("x-ig-www-claim"),
        'x-instagram-ajax': os.environ.get("x-instagram-ajax")
    }
