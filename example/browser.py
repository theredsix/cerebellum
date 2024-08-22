from cerebellum.limb.browser.planner import GeminiBrowserPlanner
from cerebellum.limb.browser.session import BrowserSession
from cerebellum.memory.file import FileSessionMemory
from playwright.sync_api import sync_playwright
import os


def wait_for_input():
    # Check for keyboard input
    input("Press enter to continue...")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    # debug_page = context.new_page()
    page.goto("https://www.amazon.com/")

    recorders = [FileSessionMemory('session.cere')]
    planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'])

    goal = "search for a usb c cable of 10 feet and add one to the cart"

    session = BrowserSession(goal, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()
