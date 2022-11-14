import pytest
from playwright.sync_api import Page
import time
from random import randint
from src.instagram import get_all_followers, login_to_instagram, get_value_from_cookies_by_key
from src.instagram import get_following_count, get_follower_count, get_all_following, get_all_likers
from src.instagram import follow_unfollow_via_api
import pandas as pd
import os
from src.supabase import new_client, n_days_ago_datetime_as_str
from postgrest.exceptions import APIError
import sys
import numpy as np


MAX_POTENCY_RATIO = 1
"""
potency_ratio with POSITIVE values can be used to route interactions to only potential (real) users WHOSE followers count is higher than following count (e.g., potency_ratio = 1.39) find desired potency_ratio with this formula: potency_ratio == followers count / following count (use desired counts)
potency_ratio with NEGATIVE values can be used to route interactions to only massive followers WHOSE following count is higher than followers count (e.g., potency_ratio = -1.42) find desired potency_ratio with this formula: potency_ratio == following count / followers count (use desired counts)
"""


@pytest.fixture()
def target_post_shortcode() -> str:
    return os.environ.get('TARGET_POST_ID')


@pytest.fixture()
def session(page: Page, username: str, password: str) -> Page:
    page.goto("https://www.instagram.com/")

    return login_to_instagram(page, username, password)


def test_unfollow_nonfollowers(session: Page, request_vars: dict):
    
    current_user_id = get_value_from_cookies_by_key(session, key='ds_user_id')

    # Get all following
    if os.path.isfile('following.csv'):
        all_following = pd.read_csv('following.csv')
    else:
        all_following = get_all_following(session, current_user_id)
        print('Saving all following to csv...')
        all_following.to_csv('following.csv', index=False)
    
    # Filter out followers
    nonfollowers = all_following.loc[~all_following['follows_viewer']]
    nonfollowers.to_csv('nonfollowers.csv', index=False)

    # Get previous_follows who were followed at least one week ago
    supabase = new_client()
    follows_from_at_least_one_week_ago = pd.DataFrame(supabase.table('follows').select('id', 'created_at').lte('created_at', n_days_ago_datetime_as_str(n_days=7)).execute().data)    

    # Cross nonfollowers with previous_follows from at least one week ago, and remove exceptions (present in the exceptions list)
    list_unfollow_exceptions = [
        55874960373  # TakesTwoDuo
    ]
    users_to_unfollow = nonfollowers.loc[
        (nonfollowers['id'].isin(follows_from_at_least_one_week_ago['id'])) & (~nonfollowers['id'].isin(list_unfollow_exceptions))
    ]

    print(f"A total of {len(users_to_unfollow)} users will be unfollowed.")
    
    def sleep_then_unfollow(session: Page, request_vars: dict, target_user_id: int) -> str:
        time.sleep(randint(3, 8))
        
        return follow_unfollow_via_api(session, request_vars, target_user_id, follow=False)

    # Execute unfollows and save to csv
    users_to_unfollow['request_response'] = users_to_unfollow.apply(
        lambda x: sleep_then_unfollow(session, request_vars, x['id']), axis=1
    )
    users_to_unfollow.to_csv('nonfollowers_from_at_east_one_week_ago.csv', index=False)


def test_follow_likers(session: Page, request_vars: dict, target_post_shortcode: str):
    print(f"Going to follow all likers of post with ID: {target_post_shortcode}")
    
    current_user_id = get_value_from_cookies_by_key(session, key='ds_user_id')

    likers_filename = f'likers_{target_post_shortcode}.csv'

    # Get all followers of target_post
    if os.path.isfile(likers_filename):
        all_likers_of_target_post = pd.read_csv(likers_filename)
    else:
        all_likers_of_target_post = get_all_likers(session, target_post_shortcode)
        print('Saving all likers to csv...')
        all_likers_of_target_post.to_csv(likers_filename, index=False)

    """
    Create function for determining whether or not to follow the target post's liker.
    If eligible, follow the liker and write a record to the database.
    """
    def follow_liker_and_write_record(liker_id: int, full_name: str, maximum_potency_ratio: float, is_private: bool, is_verified: bool) -> dict:
        following_count = get_following_count(session, liker_id)
        
        time.sleep(randint(3, 8))

        follower_count = get_follower_count(session, liker_id)
                
        time.sleep(randint(3, 8))

        """
        1 is summed to the following_count to prevent Divison by Zero.
        """
        if follower_count / (following_count + 1) < maximum_potency_ratio:
            supabase = new_client()
            previous_follows = supabase.table("follows").select("id").execute().data

            if pd.Series(previous_follows).isin([liker_id]):
                print(f'{liker_id} (full_name={full_name}) was a previous follow.')
                return 'PREVIOUS_FOLLOW'
            else:
                print(f'{liker_id} (full_name={full_name}) is a new follow.')
                
                try:
                    response = supabase.table("follows").insert({
                        'id': liker_id,
                        'full_name': full_name,
                        'follower_count': follower_count,
                        'following_count': following_count,
                        'is_private': is_private,
                        'is_verified': is_verified
                    }).execute()
                except APIError:
                    print(pd.Series(previous_follows).isin([liker_id]))
                return follow_unfollow_via_api(session, request_vars, liker_id, follow=True)

    # Only follow private accounts
    all_likers_of_target_post = all_likers_of_target_post.loc[all_likers_of_target_post['is_private'] == True]
    print(f"There's {len(all_likers_of_target_post)} private accounts.")

    all_likers_of_target_post['request_response'] = all_likers_of_target_post.apply(
        lambda x: follow_liker_and_write_record(
            x['id'], x['full_name'], MAX_POTENCY_RATIO, x['is_private'], x['is_verified']
        ) if not x['followed_by_viewer'] else 'ALREADY_FOLLOWED',
        axis=1
    )

    all_likers_of_target_post.to_csv(likers_filename, index=False)


def test_update_followers(session: Page):
    
    current_user_id = get_value_from_cookies_by_key(session, key='ds_user_id')

    # Select all followers from database
    supabase = new_client()
    previous_followers = pd.DataFrame(supabase.table("followers").select("*").execute().data)
    
    # Get updated list of followers
    current_followers = get_all_followers(session, current_user_id)
    
    # Compute previous followers who no longer follow
    union_of_followers = previous_followers.merge(current_followers, on='id', how='outer', indicator=True)

    # Determine new followers and followers who no longer follow
    no_longer_followers = union_of_followers.loc[union_of_followers['_merge'] == 'right_only']
    new_followers = union_of_followers.loc[union_of_followers['_merge'] == 'left_only']
    
    ## update nolonger followers active==false
    ## insert new_followers to DB

    # Determine nonfollowers who resumed following
    refollowers = union_of_followers.loc[(union_of_followers['_merge'] == 'both') & (union_of_followers['active'] == False)]
    ## update and set active==true and created_at==time.now() but with timezone
    
    response = supabase.table("follows").insert({
                    'id': liker_id,
                    'full_name': full_name,
                    'follower_count': follower_count,
                    'following_count': following_count,
                    'is_private': is_private,
                    'is_verified': is_verified
                }).execute()
    current_followers.to_csv('followers.csv', index=False)
