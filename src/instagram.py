from numpy import short
from playwright.sync_api import Page
import time
from random import randint
import json
import pandas as pd
import requests


"""
Main References:
https://medium.com/codex/breaking-instagram-automating-page-growth-part-1-a487c471db69
https://github.com/davidarroyo1234/InstagramUnfollowers/blob/master/src/main.js
"""


GRAPHQL_QUERY = {
    'following': '3dec7e2c57367ef3da3d987d89f9dbc8',
    'followers': 'c76146de99bb02f6415203be841dd25a',
    'likers': 'd5d763b1e2acf209d62d22d184488e57'
}

GRAPHQL_KEYS = {
    'following': ['user', 'edge_follow'],
    'followers': ['user', 'edge_followed_by'],
    'likers': ['shortcode_media', 'edge_liked_by']
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


def query_graphql_next_page(query_hash: str, page: Page, ds_user_id: int = "", first: int = 24, end_of_page_cursor: str = None, shortcode: str = "") -> str:
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
        "after": end_of_page_cursor,
        "shortcode": shortcode
    }

    params = {
        'query_hash': query_hash,
        'variables': json.dumps(variables)
    }

    query = f"{url}?query_hash={params['query_hash']}&variables={params['variables']}"

    return page.goto(query).json()


def query_graphql_all_pages(page: Page, query_type: str, ds_user_id: int = "", shortcode: str = "") -> list:
    there_is_one_more_page = True  # Initiate at True, which assumes there is a first page.
    end_of_page_cursor = None  # Initiate at None, because for the first page there is no end_of_page_cursor.
    all_following_users = []

    while there_is_one_more_page:
        try:
            next_batch_of_following_users = query_graphql_next_page(
                query_hash=GRAPHQL_QUERY[query_type], page=page, ds_user_id=ds_user_id, end_of_page_cursor=end_of_page_cursor, shortcode=shortcode
            )
        except Exception as e:
            raise e

        there_is_one_more_page = next_batch_of_following_users['data'][GRAPHQL_KEYS[query_type][0]][GRAPHQL_KEYS[query_type][1]]['page_info']['has_next_page']
        end_of_page_cursor = next_batch_of_following_users['data'][GRAPHQL_KEYS[query_type][0]][GRAPHQL_KEYS[query_type][1]]['page_info']['end_cursor']
        
        all_following_users.append(next_batch_of_following_users)

        time.sleep(randint(5, 10))  # Uniformly distributed sleep time, in seconds.
    
    return all_following_users


def get_following_or_follower_count(page: Page, ds_user_id: int, query_type: str) -> int:
    """
    If the query, for some reason, fails with JSONDecodeError, it is likely that the JSON object does not contain a body as expected.
    The most sensible action is to assume that there are no following/followers.
    """
    try:
        first_page = query_graphql_next_page(GRAPHQL_QUERY[query_type], page, ds_user_id, first=0)
    except json.decoder.JSONDecodeError:
        return 0
    
    return int(first_page['data'][GRAPHQL_KEYS[query_type][0]][GRAPHQL_KEYS[query_type][1]]['count'])


def get_following_count(page: Page, ds_user_id: int) -> int:
    return get_following_or_follower_count(page=page, ds_user_id=ds_user_id, query_type='following')


def get_follower_count(page: Page, ds_user_id: int) -> int:
    return get_following_or_follower_count(page=page, ds_user_id=ds_user_id, query_type='followers')


def get_all_following(page: Page, ds_user_id: int) -> pd.DataFrame:
    query_type = 'following'

    all_pages = query_graphql_all_pages(page, query_type=query_type, ds_user_id=ds_user_id)

    return pd.DataFrame([edge['node'] for page in all_pages for edge in page['data'][GRAPHQL_KEYS[query_type][0]][GRAPHQL_KEYS[query_type][1]]['edges']])


def get_all_followers(page: Page, ds_user_id: int) -> pd.DataFrame:
    query_type = 'followers'

    all_pages = query_graphql_all_pages(page, query_type=query_type, ds_user_id=ds_user_id)

    return pd.DataFrame([edge['node'] for page in all_pages for edge in page['data'][GRAPHQL_KEYS[query_type][0]][GRAPHQL_KEYS[query_type][1]]['edges']])


def get_all_likers(page: Page, shortcode: str) -> pd.DataFrame:
    query_type = 'likers'
        
    all_pages = query_graphql_all_pages(page, query_type=query_type, shortcode=shortcode)

    return pd.DataFrame([edge['node'] for page in all_pages for edge in page['data'][GRAPHQL_KEYS[query_type][0]][GRAPHQL_KEYS[query_type][1]]['edges']])


def follow_unfollow(*args, use_api: bool = False):
    if use_api:
        follow_unfollow_via_api(*args)
    return follow_unfollow_via_ui(*args)


def create_conversation_via_api(page: Page, request_variables: dict, list_of_recipient_user_ids: list) -> str:
    """
    NOT WORKING!
    """
    request_headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://www.instagram.com/direct/new/',
        'x-csrftoken': get_value_from_cookies_by_key(page, key='csrftoken'),  # Whereas the other request variables remain unchanged between sessions, the csrftoken must be updated.
        'x-asbd-id': request_variables['x-asbd-id'],
        'x-ig-app-id': request_variables['x-ig-app-id'],
        'x-ig-www-claim': request_variables['x-ig-www-claim'],
        'x-instagram-ajax': request_variables['x-instagram-ajax'],
        'x-requested-with': 'XMLHttpRequest'
    }
    
    response = requests.post(
        f'https://i.instagram.com/api/v1/direct_v2/create_group_thread/',
        headers=request_headers,
        data=json.dumps({'recipient_users': list_of_recipient_user_ids}),
        cookies=get_all_cookies(page)
    )
    print(f"Response {response} for users {list_of_recipient_user_ids}")
    print(response.json())
    
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code


def follow_unfollow_via_api(page: Page, request_variables: dict, target_user_id: int, follow: bool = True) -> str:
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
    
    response = requests.post(
        f'https://i.instagram.com/api/v1/web/friendships/{str(target_user_id)}/{"follow" if follow else "unfollow"}/',
        headers=request_headers,
        cookies=get_all_cookies(page)
    )
    print(f"Response {response} for user ID {str(target_user_id)}")
    
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code


def create_conversation_via_ui(page: Page, recipient_username: str) -> Page:
    """
    Create a conversation using the UI, provided the recipient_username.
    The session is assumed to already be at the "https://www.instagram.com/direct/inbox/" URL before it enters the function.
    """
    button_new_message = page.locator('button>div>svg[aria-label="New message"]')
    button_new_message.click()

    input_recipient_username = page.type('input[name="queryBox"]', recipient_username, delay=100)

    div_recipient_user = page.locator(f'div>div>div>div>div>div:text("{recipient_username}")')
    div_recipient_user.click()

    button_next = page.locator('button>div:text("Next")')
    button_next.click()

    return page


def follow_unfollow_via_ui(page: Page, target_username: str, follow: bool = True) -> str:
    page.goto(f"https://www.instagram.com/{target_username}/")
    time.sleep(randint(1, 2))

    button_follow_unfollow = page.locator(f'section>div>div>div>div>button>div>div:text(\"{"Follow" if follow else "Following"}\")')
    button_follow_unfollow.click()

    if not follow:
        time.sleep(randint(1, 2))
        button_unfollow_from_dropdown = page.locator(f'div>div>div:text("Unfollow")')
        button_unfollow_from_dropdown.click()

    print(f"{'Follow' if follow else 'Unfollow'}ed user {target_username} successfully.")
    
    return target_username


def paste_from_clipboard_to_textarea_via_ui(page: Page) -> Page:
    """
    Pastes content from the clipboard into the messaging textarea.
    Assumes the correct textarea is available.
    """
    
    message_textarea = page.locator('textarea[placeholder="Message..."]')
    message_textarea.click()

    page.keyboard.press('Control+V')

    return page


def send_message_via_ui(page: Page) -> Page:
    """
    Assumes a "Send" button is visible and enabled (message content exists).
    """

    button_send = page.locator('button:text("Send")')
    button_send.click()

    return page


def write_message_to_textarea_via_ui(page: Page, message_to_send: str) -> Page:
    """
    Assumes the correct textarea is available.
    """
    message_textarea = page.locator('textarea[placeholder="Message..."]')
    message_textarea.type(message_to_send, delay=100)

    return page
