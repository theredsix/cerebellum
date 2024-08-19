from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import html
from typing import List
from playwright.sync_api import Page

from bs4 import BeautifulSoup


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

class AbstractReasoner(ABC):
    @abstractmethod
    def get_next_action(self, goal: str, current_page: PageState, session_history: list[RecordedAction]) -> PageAction:
        pass


class AbstractBrowserSession(ABC):
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



class AbstractSessionRecorder(ABC):
    @abstractmethod
    def record(self, session: AbstractBrowserSession) -> None:
        pass

    @abstractmethod
    def record_step(self, session: AbstractBrowserSession, step: int) -> None:
        pass

    @abstractmethod
    def recover(self) -> (str, List[RecordedAction]):
        '''
        Recovers session up to this point and returns a tuple of goal, list[RecordedActions]
        '''
        pass


class AbstractHTMLSensor(ABC):
    @abstractmethod
    def sense(self, page: Page) -> str:
        pass    