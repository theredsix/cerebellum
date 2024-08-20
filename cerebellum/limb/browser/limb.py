from cerebellum.core_abstractions import AbstractLimb
from .types import BrowserAction, BrowserActionOutcome, BrowserActionResult
from playwright.sync_api import Page, TimeoutError

class BrowserLimb(AbstractLimb[BrowserAction, BrowserActionResult]):

    def __init__(self, page: Page):
        super().__init__()
        self.page = page

    def perform_action(self, action: BrowserAction) -> BrowserActionResult:
        
        function_name = action.function
        params = action.args
        outcome: BrowserActionOutcome = None
        
        print(f"INTENT: {action.reason}")

        # Ensure the css_selector can select an element if provided
        if 'css_selector' in params:
            css_selector = params['css_selector']
            element = self.page.query_selector(css_selector)
            if element is None:
                print(f"Warning: No element found for selector '{css_selector}'")
                outcome = BrowserActionOutcome['INVALID_CSS_SELECTOR']

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
                            outcome = BrowserActionOutcome['SUCCESS']
                        except Exception as e:
                            if "Element is not an <input>" in str(e):
                                print(f"Error: Element with selector '{css_selector}' is not fillable")
                                outcome = BrowserActionOutcome['NONFILLABLE_CSS_SELECTOR']
                            else:
                                raise  # Re-raise the exception
                    
                    case "click":
                        css_selector = params["css_selector"]
                        print(f"Clicking element: selector='{css_selector}'")
                        self.page.click(css_selector)
                        outcome = BrowserActionOutcome['SUCCESS']

                    case "focus":
                        css_selector = params["css_selector"]
                        print(f"Focusing on element: selector='{css_selector}'")
                        self.page.focus(css_selector)
                        outcome = BrowserActionOutcome['SUCCESS']
                    
                    case "achieved":
                        print("Goal achieved!")
                        outcome = BrowserActionOutcome['GOAL_ACHIEVED']
                    
                    case "unreachable":
                        print("Goal unreachable.")
                        outcome = BrowserActionOutcome['GOAL_UNREACHABLE']
            except TimeoutError:
                print(f"Timeout error occurred while performing action: {function_name}")
                outcome = BrowserActionOutcome['TIMEOUT']

        # Inject at least 1 second wait for action to be processed
        self.page.wait_for_timeout(500)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(500)
    
        is_terminal_state = outcome in [BrowserActionOutcome['GOAL_ACHIEVED'], BrowserActionOutcome['GOAL_UNREACHABLE']]
        return BrowserActionResult(url=self.page.url, outcome=outcome, is_terminal_state=is_terminal_state)