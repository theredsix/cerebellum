from browser.planner.local import LocalLLMBrowserPlanner
from browser.planner.planner import HumanBrowserPlanner, GeminiBrowserPlanner
from cerebellum.browser.session import BrowserSession
from cerebellum.memory.file import FileSessionMemory
from playwright.sync_api import sync_playwright
import os

def create_radio_buttons_page(page):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Radio Buttons Example</title>
    </head>
    <body>
        <h1>Select an option:</h1>
        <form>
            <input type="radio" id="option1" name="choice" value="option1" checked>
            <label for="option1">Option 1</label><br>
            
            <input type="radio" id="option2" name="choice" value="option2">
            <label for="option2">Option 2</label><br>
            
            <input type="radio" id="option3" name="choice" value="option3">
            <label for="option3">Option 3</label><br>
        </form>
    </body>
    </html>
    """
    page.set_content(html_content)



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
    create_radio_buttons_page(page);
    # page.goto("https://www.dmv.ca.gov/")

    recorders = [FileSessionMemory('radio.cere.zip')]
    base_planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'], model_name='gemini-1.5-pro-exp-0827')
    # base_planner = OpenAIBrowserPlanner(api_key=os.environ['OPENAI_API_KEY'], model_name="gpt-4o-mini")
    # base_planner = OpenAIBrowserPlanner(api_key="ollama", model_name="llama3.1:8b-instruct-fp16", origin="http://localhost:11434")
    # base_planner = LocalLLMBrowserPlanner()

    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Select radio button 3"

    session = BrowserSession(goal, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()
