import os
from playwright.sync_api import sync_playwright, expect

auth_file = os.path.join(os.path.dirname(__file__), '../.auth/user.json')

def authenticate(page):
    # Perform authentication steps. Replace these actions with your own.
    page.goto('https://github.com/login')

    # End of authentication steps.
    input('Press enter to complete auth')

    page.context.storage_state(path=auth_file)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    authenticate(page)    
    browser.close()