from limb.browser.local import LocalLLMBrowserPlanner
from cerebellum.browser.planner import GeminiBrowserPlanner, HumanBrowserPlanner, OpenAIBrowserPlanner
from cerebellum.browser.session import BrowserSession
from cerebellum.memory.file import FileSessionMemory
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
    page.goto("https://www.dmv.ca.gov/")

    recorders = [FileSessionMemory('session.cere')]
    # base_planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'])
    # base_planner = OpenAIBrowserPlanner(api_key=os.environ['OPENAI_API_KEY'], model_name="gpt-4o-mini")
    base_planner = OpenAIBrowserPlanner(api_key="ollama", model_name="llama3.1:8b-instruct-fp16", origin="http://localhost:11434")
    base_planner = LocalLLMBrowserPlanner()

    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Complete the vehicle registration renewal for License Plate 7WDR747 with VIN 08969"

    session = BrowserSession(goal, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()
