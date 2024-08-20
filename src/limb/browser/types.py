from dataclasses import dataclass
from src.core_abstractions import ActionOutcome, ActionResult

class BrowserActionOutcome(ActionOutcome):
    SUCCESS = "Action performed."
    INVALID_CSS_SELECTOR = "Action failed. Invalid CSS selector did not match to any elements."
    NONFILLABLE_CSS_SELECTOR = "Action failed. First element targeted by CSS selector was not a <input>, <textarea> or [contenteditable]."
    TIMEOUT = "Action failed. Playwright timed out while attempting to perform the requested action."

@dataclass
class BrowserState:
    html: str
    raw_html: str
    screenshot_full: str
    screenshot_viewport: str
    url: str

@dataclass
class BrowserAction:
    function: str
    args: dict[str, str] # arg-name: arg-value
    reason: str # Reason for taking this action

@dataclass
class BrowserActionResult(ActionResult):
    url: str
    outcome: BrowserActionOutcome
