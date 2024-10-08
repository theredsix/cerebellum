from browser.planner.local import LocalLLMBrowserPlanner
from cerebellum import FileSessionMemory, BrowserSession, GeminiBrowserPlanner, HumanBrowserPlanner, OpenAIBrowserPlanner
from playwright.sync_api import sync_playwright
import os

auth_file = os.path.join(os.path.dirname(__file__), '../.auth/user.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(storage_state=auth_file)
    context.tracing.start(screenshots=True)
    page = context.new_page()
    control_page = context.new_page()
    # debug_page = context.new_page()
    page.goto("https://www.github.com/")

    recorders = [FileSessionMemory('session.cere')]
    # base_planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'], model_name='gemini-1.5-pro-exp-0827')
    base_planner = OpenAIBrowserPlanner(api_key=os.environ['OPENAI_API_KEY'], model_name="gpt-4o-mini", vision_capabale=False)
    # base_planner = LocalLLMBrowserPlanner()

    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Navigate to my settings and show me my SSH keys"

    session = BrowserSession(goal, page, planner=planner, recorders=recorders)

    input("Press enter to continue...")

    session.start()

    input("Press enter to continue...")

    browser.close()
