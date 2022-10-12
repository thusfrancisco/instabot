from playwright.sync_api import Page
import time
from random import randint
import json
import pandas as pd
import requests


GRAPHQL_QUERY = {
    'following': '3dec7e2c57367ef3da3d987d89f9dbc8',
    'followers': 'c76146de99bb02f6415203be841dd25a'
}


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


def get_value_from_cookies_by_key(page: Page, key: str) -> str:
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


def get_all_cookies(page: Page) -> dict:
    cookies_list = page.context.cookies()

    return {
        cookie['name']: cookie['value'] for cookie in cookies_list
    }


def query_graphql_next_page(query_hash: str, page: Page, ds_user_id: int, first: int = 24, end_of_page_cursor: str = None) -> str:
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
        'query_hash': query_hash,
        'variables': json.dumps(variables)
    }

    query = f"{url}?query_hash={params['query_hash']}&variables={params['variables']}"

    return page.goto(query).json()


def query_graphql_all_pages(page: Page, ds_user_id: int, query_type: str) -> list:
    there_is_one_more_page = True  # Initiate at True, which assumes there is a first page.
    end_of_page_cursor = None  # Initiate at None, because for the first page there is no end_of_page_cursor.
    all_following_users = []

    while there_is_one_more_page:
        try:
            next_batch_of_following_users = query_graphql_next_page(query_hash=GRAPHQL_QUERY[query_type], page=page, ds_user_id=ds_user_id, end_of_page_cursor=end_of_page_cursor)
        except Exception as e:
            raise e

        there_is_one_more_page = next_batch_of_following_users['data']['user']['edge_follow']['page_info']['has_next_page']
        end_of_page_cursor = next_batch_of_following_users['data']['user']['edge_follow']['page_info']['end_cursor']
        
        all_following_users.append(next_batch_of_following_users)

        time.sleep(randint(5, 10))  # Uniformly distributed sleep time, in seconds.
    
    return all_following_users


def get_following_count(page: Page, ds_user_id: int) -> int:
    first_page = query_graphql_next_page(GRAPHQL_QUERY['following'], page, ds_user_id, first=0)

    return int(first_page['data']['user']['edge_follow']['count'])


def get_follower_count(page: Page, ds_user_id: int) -> int:
    first_page = query_graphql_next_page(GRAPHQL_QUERY['followers'], page, ds_user_id, first=0)

    return int(first_page['data']['user']['edge_follow']['count'])


def get_all_following(page: Page, ds_user_id: int) -> pd.DataFrame:
    all_pages = query_graphql_all_pages(page, ds_user_id, 'following')

    return pd.DataFrame([edge['node'] for page in all_pages for edge in page['data']['user']['edge_follow']['edges']])


def get_all_followers(page: Page, ds_user_id: int) -> pd.DataFrame:
    all_pages = query_graphql_all_pages(page, ds_user_id, 'followers')

    return pd.DataFrame([edge['node'] for page in all_pages for edge in page['data']['user']['edge_follow']['edges']])


def follow_unfollow_via_api(page: Page, request_variables: dict, target_user: str, follow: bool = True) -> str:
    request_headers = {
        'accept': '*/*',
        'accept-language': 'en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'x-csrftoken': get_value_from_cookies_by_key(page, key='csrftoken'),  # Whereas the other request variables remain unchanged between sessions, the csrftoken must be updated.
        'x-asbd-id': request_variables['x-asbd-id'],
        'x-ig-app-id': request_variables['x-ig-app-id'],
        'x-ig-www-claim': request_variables['x-ig-www-claim'],
        'x-instagram-ajax': request_variables['x-instagram-ajax'],
        'x-requested-with': 'XMLHttpRequest'
    }
    
    return requests.post(
        f'https://i.instagram.com/api/v1/web/friendships/{target_user}/{"follow" if follow else "unfollow"}/',
        headers=request_headers,
        cookies=get_all_cookies(page)
    ).json()

"""
saber n0 followers
calcular 
"""