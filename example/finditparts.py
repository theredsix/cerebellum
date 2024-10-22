# from browser.planner.local import LocalLLMBrowserPlanner
from cerebellum import FileSessionMemory, BrowserSession, GeminiBrowserPlanner, HumanBrowserPlanner, OpenAIBrowserPlanner
from playwright.sync_api import sync_playwright
import os


def wait_for_input():
    # Check for keyboard input
    input("Press enter to continue...")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True)
    page = context.new_page()
    control_page = context.new_page()
    # debug_page = context.new_page()
    # page.goto("https://www.dmv.ca.gov/")
    page.goto("https://www.finditparts.com")

    recorders = [FileSessionMemory('finditparts.cere.zip')]
    # base_planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'], model_name='gemini-1.5-pro-exp-0827')
    base_planner = OpenAIBrowserPlanner(api_key=os.environ['OPENAI_API_KEY'], model_name="gpt-4o-mini")
    # base_planner = LocalLLMBrowserPlanner()

    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Search for the specified product id, add it to cart and then navigate to the cart page"
    additional_context = {
        "product_id": "W01-377-8537",
    }

    session = BrowserSession(goal, additional_context, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()