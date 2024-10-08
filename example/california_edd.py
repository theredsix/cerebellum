from browser.planner.local import LocalLLMBrowserPlanner
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
    page.goto("https://eddservices.edd.ca.gov/acctservices/AccountManagement/AccountServlet?Command=NEW_SIGN_UP")

    recorders = [FileSessionMemory('edd.cere.zip')]
    # base_planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'], model_name='gemini-1.5-pro-exp-0827')
    base_planner = OpenAIBrowserPlanner(api_key=os.environ['OPENAI_API_KEY'], model_name="gpt-4o-mini")
    # base_planner = LocalLLMBrowserPlanner()

    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Navigate through the employer services online enrollment form. Terminate when the form is completed"
    additional_context = {
        "username": "isthisreal1",
        "password": "Password123!",
        "first_name": "John",
        "last_name": "Doe",
        "pin": "1234",
        "email": "isthisreal1@gmail.com",
        "phone_number": "412-444-1234",
    }

    session = BrowserSession(goal, additional_context, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()
