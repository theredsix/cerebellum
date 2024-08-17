from dataclasses import dataclass
import html
from playwright.sync_api import Page, TimeoutError
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from enum import Enum
from html_utils import get_visible_html
from base64 import b64encode

@dataclass
class PageState:
    html: str
    screenshot_full: str
    screenshot_viewport: str
    url: str

@dataclass
class PageAction:
    function: str
    args: dict[str, str] # arg-name: arg-value
    reason: str # Reason for taking this action

class ActionOutcome(Enum):
    SUCCESS = "Action performed."
    INVALID_CSS_SELECTOR = "Action failed. Invalid CSS selector did not match to any elements."
    NONFILLABLE_CSS_SELECTOR = "Action failed. First element targeted by CSS selector was not a <input>, <textarea> or [contenteditable]."
    TIMEOUT = "Action failed. Playwright timedout while attempting to perform the requested action."
    GOAL_ACHIEVED = "Goal achieved."
    GOAL_UNREACHABLE = "Goal is unreachable."

@dataclass
class ActionResult:
    url: str
    outcome: ActionOutcome

@dataclass
class RecordedAction:
    state: PageState
    action: PageAction
    result: ActionResult

class Reasoner(ABC):
    @abstractmethod
    def get_next_action(self, goal: str, current_page: PageState, session_history: list[RecordedAction]) -> PageAction:
        pass


class BrowserSession(ABC):
    page: Page
    goal: str
    actions: list[RecordedAction]

    def __init__(self, goal: str, page: Page, actions: list[RecordedAction] = None):
        self.goal = goal
        self.page = page
        self.actions = actions if actions is not None else []

    def display_state(self, step: int = -1, page: Page = None):
        if page is None:
            page = self.page

        action = self.actions[step]
        
        # Parse and pretty print the HTML content        
        soup = BeautifulSoup(action.state.html, 'html.parser')
        pretty_html = html.escape(soup.prettify())
        
        # Create an HTML document with viewport screenshot, full screenshot, pretty-printed HTML, action, and result
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser Session State - Step {step}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h2 {{ color: #333; }}
        img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin-bottom: 20px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f5f5f5; padding: 15px; border: 1px solid #ddd; }}
        .action-result {{ background-color: #e6f3ff; padding: 15px; border: 1px solid #b8d4ff; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h2>Action</h2>
    <div class="action-result">
        <p><strong>Intent:</strong> {action.action.reason}</p>
        <p><strong>Function:</strong> {action.action.function}</p>
        <p><strong>Arguments:</strong> {'<br>'.join([f"{k}: {v}" for k, v in action.action.args.items()])}</p>
    </div>

    <h2>Result</h2>
    <div class="action-result">
        <p><strong>URL:</strong> {action.result.url}</p>
        <p><strong>Outcome:</strong> {action.result.outcome}</p>
    </div>

    <h2>Viewport Screenshot</h2>
    <img src="data:image/png;base64,{action.state.screenshot_viewport}" alt="Viewport Screenshot">
    
    <h2>Full Page Screenshot</h2>
    <img src="data:image/png;base64,{action.state.screenshot_full}" alt="Full Page Screenshot">
    
    <h2>Page HTML</h2>
    <pre>{pretty_html}</pre>
</body>
</html>
        """
        
        # Set the content of the page to our created HTML
        page.set_content(html_content)


    

class RecordedBrowserSession(BrowserSession):

    def __init__(self, goal: str, page: Page, actions: list[RecordedAction]):
        super().__init__(goal, page, actions)
        if not actions:
            raise ValueError("RecordedBrowserSession requires a non-empty list of actions")

class ActiveBrowserSession(BrowserSession):
    reasoner: Reasoner

    def __init__(self, goal: str, page: Page, reasoner: Reasoner):
        super().__init__(goal, page)
        self.reasoner = reasoner

    def perform_action(self, action: PageAction) -> ActionResult:
        
        function_name = action.function
        params = action.args
        outcome: ActionOutcome = None
        
        print(f"INTENT: {action.reason}")

        # Ensure the css_selector can select an element if provided
        if 'css_selector' in params:
            css_selector = params['css_selector']
            element = self.page.query_selector(css_selector)
            if element is None:
                print(f"Warning: No element found for selector '{css_selector}'")
                outcome = ActionOutcome.INVALID_CSS_SELECTOR

        while outcome is None:
            try:
                match function_name:
                    case "fill":
                        # Ensure the element is fillable
                        element = self.page.query_selector(params["css_selector"])
                        css_selector = params["css_selector"]
                        text = params["text"]
                        press_enter = params.get("press_enter", False)
                        print(f"Filling input: selector='{css_selector}', text='{text}', press_enter={press_enter}")
                        try:
                            self.page.fill(css_selector, text)
                            if press_enter:
                                self.page.press(css_selector, "Enter")
                            outcome = ActionOutcome.SUCCESS
                        except Exception as e:
                            if "Element is not an <input>" in str(e):
                                print(f"Error: Element with selector '{css_selector}' is not fillable")
                                outcome = ActionOutcome.NONFILLABLE_CSS_SELECTOR
                    
                    case "click":
                        css_selector = params["css_selector"]
                        print(f"Clicking element: selector='{css_selector}'")
                        self.page.click(css_selector)
                        outcome = ActionOutcome.SUCCESS

                    case "focus":
                        css_selector = params["css_selector"]
                        print(f"Focusing on element: selector='{css_selector}'")
                        self.page.focus(css_selector)
                        outcome = ActionOutcome.SUCCESS
                    
                    case "achieved":
                        print("Goal achieved!")
                        outcome = ActionOutcome.GOAL_ACHIEVED
                    
                    case "unreachable":
                        print("Goal unreachable.")
                        outcome = ActionOutcome.GOAL_UNREACHABLE
            except TimeoutError:
                print(f"Timeout error occurred while performing action: {function_name}")
                outcome = ActionOutcome.TIMEOUT
        
        print("No terminal action called, continuing...")
        return ActionResult(self.page.url, outcome)

    def step(self):
        # Gather current state
        current_state = PageState(
            html=get_visible_html(self.page),
            screenshot_full=b64encode(self.page.screenshot(full_page=True)).decode('utf-8'),
            screenshot_viewport=b64encode(self.page.screenshot(full_page=False)).decode('utf-8'),
            url=self.page.url
        )

        # Get next action from reasoner
        next_action = self.reasoner.get_next_action(self.goal, current_state, self.actions)

        # Perform the action
        action_result = self.perform_action(next_action)

        # Record the action
        recorded_action = RecordedAction(
            state=current_state,
            action=next_action,
            result=action_result
        )
        self.actions.append(recorded_action)

        return action_result
    
    def start(self):
        while len(self.actions) == 0 or \
        self.actions[-1].result.outcome != ActionOutcome.GOAL_ACHIEVED or \
        self.actions[-1].result.outcome != ActionOutcome.GOAL_UNREACHABLE:
            self.step()


    