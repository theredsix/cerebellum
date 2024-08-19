from typing import List
from playwright.sync_api import Page, TimeoutError
from base64 import b64encode
from src.html_utils import AbstractHTMLSensor, VisibleHTMLSensor
from src.abstracts import (
    AbstractSessionRecorder, AbstractBrowserSession, ActionOutcome,
    ActionResult, PageAction, PageState, AbstractReasoner, RecordedAction
)

class RecordedBrowserSession(AbstractBrowserSession):

    def __init__(self, goal: str, page: Page, actions: list[RecordedAction]):
        super().__init__(goal, page, actions)
        if not actions:
            raise ValueError("RecordedBrowserSession requires a non-empty list of actions")

class ActiveBrowserSession(AbstractBrowserSession):
    reasoner: AbstractReasoner
    html_extractor: AbstractHTMLSensor
    recorder: List[AbstractSessionRecorder]

    def __init__(self, goal: str, page: Page, reasoner: AbstractReasoner, 
                 html_extractor: AbstractHTMLSensor = None, recorders: List[AbstractSessionRecorder] = None):
        super().__init__(goal, page)
        self.reasoner = reasoner
        self.html_extractor = html_extractor if html_extractor is not None else VisibleHTMLSensor()
        self.recorders = recorders if recorders is not None else []

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
                            else:
                                raise  # Re-raise the exception
                    
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
            html=self.html_extractor.sense(self.page),
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

        # Call the recorder if it exists
        for recorder in self.recorders:
            recorder.record_step(self, len(self.actions) - 1)

        return action_result
    
    def start(self):
        while (not self.actions or
               self.actions[-1].result.outcome not in [ActionOutcome.GOAL_ACHIEVED,
                                                       ActionOutcome.GOAL_UNREACHABLE]):
            self.step()


    