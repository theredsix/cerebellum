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
    # debug_page = context.new_page()
    page.goto("https://calendly.com/han-wang")

    wait_for_input()

    context.tracing.stop(path='calendly.zip')

    browser.close()
