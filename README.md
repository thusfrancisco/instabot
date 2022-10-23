# Instabot

This is an open source project to automate certain tasks for Instagram.
I do not advise its use, as it goes against Instagram's terms of service, and thus could potentially result in a ban.

This project was created as a simple, straightforward implementation, using Playwright for Python.

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

Once these steps have been completed, you can execute any of the functions in the ``main.py`` file by using the ``pytest`` command:

    pytest --headed main.py -k 'test_name' -s

Where the ``--headed`` option forces Playwright to not use a headless browser (which Instagram does not accept), the ``-k`` option allows you to specify the test to run, and ``-s`` forces pytest to print everything to the terminal.