from playwright.sync_api import Page
import time
from random import randint
import json


def login_to_instagram(page, username, password) -> Page:
    """
    Answer the cookies dialog,
    type username and password,
    and close the two ensuing dialogs (deny saving login info and don't turn on notifications).
    """
    
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

    return page


def get_value_from_cookies_by_key(page, key: str) -> str:
    cookies = page.context.cookies()

    """
    I considered using alternative solutions.
    I think this is one of the fastest ways to get the user id, for two reasons:
        The computation done at each step is almost nothing.
        The iteration is likely to end prematurely, as soon as the user id is found.
    An interesting alternative would be to use pandas instead,
    simply converting the list of dictionaries into a dataframe.
    """
    i = 0
    while cookies[i]['name'] != key:
        i += 1

    return cookies[i]['value']


def get_following_users_next_page(page: Page, ds_user_id: int, first: int = 24, end_of_page_cursor: str = None) -> str:
    """
    The graphql query is used to get a batch of users and related information.
    To prevent timeouts, the number of users collected per query is 24 ("first":"24").
    For this reason, to get any users beyond the first 24, the cursor value for the end of page must be provided.

    Using page.goto() was the easiest way to provide context to the request.
    Using the requests module, for instance, would require many arguments and information to be provided.
    """
    url = 'https://www.instagram.com/graphql/query/'

    variables = {
        "id": ds_user_id,
        "first": first,
        "after": end_of_page_cursor
    }

    params = {
        'query_hash': '3dec7e2c57367ef3da3d987d89f9dbc8',
        'variables': json.dumps(variables)
    }

    query = f"{url}?query_hash={params['query_hash']}&variables={params['variables']}"

    return page.goto(query).json()


def get_all_following_users(page: Page, ds_user_id: int):
    there_is_one_more_page = True  # Initiate at True, which assumes there is a first page.
    end_of_page_cursor = None  # Initiate at None, because for the first page there is no end_of_page_cursor.

    while there_is_one_more_page:
        try:
            next_batch_of_following_users = get_following_users_next_page(page, ds_user_id, end_of_page_cursor)
        except Exception as e:
            raise e

        there_is_one_more_page = json.loads(next_batch_of_following_users).data.user.edge_follow.page_info.has_next_page
        
        all_following_users += next_batch_of_following_users

        time.sleep(randint(10, 30))  # Uniformly distributed sleep time, in seconds.
    
    return all_following_users
