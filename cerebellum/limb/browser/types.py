from dataclasses import dataclass
from enum import Enum
from typing import List
from cerebellum.core_abstractions import BaseAction, BaseResult, BaseState

BrowserActionOutcome = {
    'SUCCESS' : "Action performed.",
    'INVALID_TARGET_ELEMENT' : "Action failed. Target element did not match to any elements.",
    'NONFILLABLE_TARGET_ELEMENT' : "Action failed. Target element was not able to be filled by the provided value.",
    'TIMEOUT' : "Action failed. Playwright timed out while attempting to perform the requested action.",
    'GOAL_ACHIEVED' : "Goal achieved.",
    'GOAL_UNREACHABLE' : "Goal is unreachable.",
}

@dataclass
class BrowserState(BaseState):
    html: str
    raw_html: str
    screenshot_full: str
    screenshot_viewport: str
    url: str
    fillable_selectors: List[str]
    clickable_selectors: List[str]

@dataclass
class BrowserAction(BaseAction):
    function: str
    args: dict[str, str] # arg-name: arg-value
    reason: str # Reason for taking this action

@dataclass
class BrowserActionResult(BaseResult):
    url: str
    outcome: str
