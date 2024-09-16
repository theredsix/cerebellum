from cerebellum.browser.planner import GeminiBrowserPlanner, HumanBrowserPlanner
from cerebellum.browser.session import BrowserSession
from cerebellum.memory.file import FileSessionMemory
from playwright.sync_api import sync_playwright
import os


def wait_for_input():
    # Check for keyboard input
    input("Press enter to continue...")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.3')
    context.tracing.start(screenshots=True)
    page = context.new_page()
    control_page = context.new_page()
    # debug_page = context.new_page()
    page.goto("https://www.sfmta.com/onlinecitation")

    recorders = [FileSessionMemory('session.cere')]
    base_planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'])
    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Find all outstanding parking tickets for license plate 7WDR747 registered in California"

    session = BrowserSession(goal, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()
