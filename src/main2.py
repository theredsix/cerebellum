from gemini import GoogleGeminiReasoner
from session import ActiveBrowserSession
from playwright.sync_api import sync_playwright
import os

def wait_for_input():
    while True:
        # Check for keyboard input
        input("Press enter to continue...")
        break


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    debug_page = context.new_page()
    page.goto("https://www.amazon.com/")

    reasoner = GoogleGeminiReasoner(api_key=os.environ['GEMINI_API_KEY'])

    goal = "search for a usb c cable of 10 feet and it to cart"

    session = ActiveBrowserSession(goal, page, reasoner)

    wait_for_input()

    while True:
        session.step()
        session.display_state(page=debug_page)
        wait_for_input()

    browser.close()
