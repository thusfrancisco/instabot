# Instabot

    ⚠ Disclaimer: For educational purposes only! I do not advise the usage of the code in this repository, as it goes against Instagram's terms of service, and thus could potentially result in a ban.

This is an open source project to automate certain tasks for Instagram. Though it can be forked and used as such, it cannot automate interactions, such as liking posts and writing comments.
It can only manage relationships by automating the process of following and unfollowing users.

This project was created as a simple, straightforward implementation, using Playwright for Python, in contrast to most projects which use elaborate implementations. This project uses a mix of the Instagram APIs (both the REST and GraphQL ones), as well as traditional scraping tools.

## Setup

To use this project, you must install the required dependencies from the ``requirements.txt`` file, using ``pip install``.
The next step is to setup environment variables. The ones currently being used are:

- **Instagram credentials:**
    - INSTA_USERNAME
    - INSTA_PASSWORD
    - COOKIE_DS_USER_ID
- **Instagram persistent session cookies (open an Instagram session, and use CTRL+SHIFT+I):**
    - x-asbd-id
    - x-ig-app-id
    - x-ig-www-claim
    - x-instagram-ajax
- **Supabase credentials:**
    - SUPABASE_URL
    - SUPABASE_KEY
- **Post from which to scrape the likers:**
    - TARGET_POST_ID

This project makes use of the ``pytest-dotenv`` module, which allows you to simply write all necessary environment variables to a ``.env`` file.

To find the **TARGET_POST_ID**, open an Instagram session, select the likes of the post whose likers you want to follow and see what is the shortcode of the response of the last GraphQL query executed by the client. ``shortcode`` is the post ID you're looking for.

Once these steps have been completed, you can execute any of the functions in the ``main.py`` file by using the ``pytest`` command:

    pytest --headed main.py -k 'test_name' -s

Where the ``--headed`` option forces Playwright to not use a headless browser (which Instagram does not accept), the ``-k`` option allows you to specify the test to run, and ``-s`` forces pytest to print everything to the terminal.