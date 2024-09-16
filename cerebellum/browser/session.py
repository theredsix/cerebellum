from typing import List
from playwright.sync_api import Page
from cerebellum.browser.limb import BrowserLimb
from cerebellum.browser.sensor import BrowserSensor
from cerebellum.browser.types import BrowserAction, BrowserActionResult, BrowserState
from core import (
    AbstractLimb, AbstractPlanner, AbstractSensor, AbstractSession, AbstractSessionRecorder, RecordedAction
)

class BrowserSession(AbstractSession[BrowserState, BrowserAction, BrowserActionResult]):

    def __init__(self, goal: str, limb: AbstractLimb[BrowserAction, BrowserActionResult], 
            sensor: AbstractSensor[BrowserState], 
            planner: AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult], 
            recorders: 'List[AbstractSessionRecorder[BrowserState, BrowserAction, BrowserActionResult]]' = [],
            past_actions: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]] = []):
        super().__init__(
            goal=goal,
            limb=limb,
            sensor=sensor,
            planner=planner,
            recorders=recorders,
            past_actions=past_actions
        )

    def __init__(self, goal: str, page: Page, planner: AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult], 
            recorders: 'List[AbstractSessionRecorder[BrowserState, BrowserAction, BrowserActionResult]]' = [],
            past_actions: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]] = []):
        limb = BrowserLimb(page)
        sensor = BrowserSensor(page)
        super().__init__(
            goal=goal,
            limb=limb,
            sensor=sensor,
            planner=planner,
            recorders=recorders,
            past_actions=past_actions
        )