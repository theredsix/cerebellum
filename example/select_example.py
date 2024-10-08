from browser.planner.local import LocalLLMBrowserPlanner
from cerebellum import HumanBrowserPlanner, OpenAIBrowserPlanner, BrowserSession, FileSessionMemory
from playwright.sync_api import sync_playwright
import os

def create_dropdown_page(page):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dropdown Select Example</title>
    </head>
    <body>
        <h1>Select an option:</h1>
        <form>
            <label for="cars">Choose a car:</label>
            <select id="cars" name="cars" multiple>
                <option value="">--Please choose an option--</option>
                <option value="volvo">Volvo</option>
                <option value="saab">Saab</option>
                <option value="mercedes">Mercedes</option>
                <option value="audi">Audi</option>
            </select>
        </form>
    </body>
    </html>
    """
    page.set_content(html_content)

def wait_for_input():
    input("Press enter to continue...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True)
    page = context.new_page()
    control_page = context.new_page()
    create_dropdown_page(page)

    recorders = [FileSessionMemory('session.cere')]
    # base_planner = OpenAIBrowserPlanner(api_key=os.environ['OPENAI_API_KEY'], model_name="gpt-4o-mini")
    base_planner = LocalLLMBrowserPlanner()
    planner = HumanBrowserPlanner(base_planner, control_page)

    goal = "Select 'Mercedes' and 'Saab' from the dropdown menu"

    session = BrowserSession(goal, page, planner=planner, recorders=recorders)

    wait_for_input()

    session.start()

    wait_for_input()

    browser.close()
