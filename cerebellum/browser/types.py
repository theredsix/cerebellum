from dataclasses import dataclass
from typing import List, Dict
from core import BaseAction, BaseResult, BaseState

BrowserActionOutcome = {
    'SUCCESS' : "Action performed.",
    'INVALID_TARGET_ELEMENT' : "Action failed. Target element did not match to any elements.",
    'NONFILLABLE_TARGET_ELEMENT' : "Action failed. Target element was not able to be filled by the provided value.",
    'INVALID_SELECT_VALUE' : "Action failed. Target select element did not take the provided value.",
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
    selectable_selectors: Dict[str, List[str]]
    checkable_selectors: List[str]
    input_state: Dict[str, str]

@dataclass
class BrowserAction(BaseAction):
    function: str
    args: Dict[str, str] # arg-name: arg-value
    prior_steps: str
    current_state: str
    top_5_actions: List[str]
    action_analysis: str

@dataclass
class BrowserActionResult(BaseResult):
    url: str
    outcome: str
