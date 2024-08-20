from cerebellum.limb.browser.planner import GoogleGeminiReasoner
from cerebellum.limb.browser.session import ActiveBrowserSession
from cerebellum.recorders import PageActionRecorder, FileSessionRecorder, PausingRecorder
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
    debug_page = context.new_page()
    page.goto("https://www.amazon.com/")

    recorders = [FileSessionRecorder('session.cere'), PageActionRecorder(debug_page), PausingRecorder()]
    reasoner = GoogleGeminiReasoner(api_key=os.environ['GEMINI_API_KEY'])

    goal = "search for a usb c cable of 10 feet and add one to the cart"

    session = ActiveBrowserSession(goal, page, reasoner, recorders=recorders)

    wait_for_input()

    session.start()

    browser.close()
