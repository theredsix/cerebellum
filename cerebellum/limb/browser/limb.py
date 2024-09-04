from cerebellum.core_abstractions import AbstractLimb
from .types import BrowserAction, BrowserActionOutcome, BrowserActionResult
from playwright.sync_api import Page, TimeoutError, Error

class BrowserLimb(AbstractLimb[BrowserAction, BrowserActionResult]):

    def __init__(self, page: Page):
        super().__init__()
        self.page = page

    @classmethod
    def target_element_to_css_selector(self, target_element):
        if target_element.get('element_id'):
            return f"#{target_element['element_id']}"
        
        selector_parts = []
        
        selector_parts.append(target_element['tag'])
        
        if 'css_classes' in target_element:
            selector_parts.extend([f".{cls}" for cls in target_element['css_classes']])
        
        return ''.join(selector_parts)
    
    @classmethod
    def are_element_handles_equal(cls, handle1, handle2):
        return handle1.evaluate("(el1, el2) => el1 === el2", handle2)
    

    @classmethod
    def strip_unnecessary_escaped_char(cls, css_selector: str) -> str:
        return css_selector.encode().decode('unicode_escape')

    def perform_action(self, action: BrowserAction) -> BrowserActionResult:
        
        function_name = action.function
        params = action.args
        outcome: BrowserActionOutcome = None
        starting_url = self.page.url    
        
        print(f"INTENT: {action.reason}")

        # Ensure the css_selector can select an element if provided
        target_element = None
        if 'css_selector' in params:
            try:
                css_selector = params['css_selector']
                print('css_selector', css_selector)

                css_selector = BrowserLimb.strip_unnecessary_escaped_char(css_selector)

                if ':contains(' in css_selector:
                    # Replace :contains( with :has-text(
                    css_selector = css_selector.replace(':contains(', ':has-text(')

                    print('contains_text', css_selector)
                    
                print('Final css_selector', css_selector)

                target_element = self.page.locator(css_selector).nth(0)

                print(target_element)

            except Error:
                pass
            
            if target_element is None:
                print(f"Warning: No element found for selector '{css_selector}'")
                outcome = BrowserActionOutcome['INVALID_TARGET_ELEMENT']


        after_action_delay = 100

        while outcome is None:
            try:
                match function_name:
                    case "fill":
                        # Ensure the element is fillable
                        text = params["text"]
                        press_enter = params.get("press_enter", False)
                        print(f"Filling input: selector='{css_selector}', text='{text}', press_enter={press_enter}")
                        try:
                            target_element.fill(text)

                            # Verify that the target_element has been set to the required text
                            self.page.wait_for_timeout(100)
                            actual_text = target_element.input_value()
                            if actual_text != text:
                                print(f"Warning: Element text mismatch. Expected '{text}', but got '{actual_text}'")
                                outcome = BrowserActionOutcome['NONFILLABLE_TARGET_ELEMENT']

                            if press_enter:
                                target_element.press("Enter")
                            
                            outcome = BrowserActionOutcome['SUCCESS']
                        except Exception as e:
                            if "Element is not an <input>" in str(e):
                                print(f"Error: Element with selector '{css_selector}' is not fillable")
                                outcome = BrowserActionOutcome['NONFILLABLE_TARGET_ELEMENT']
                            else:
                                raise  # Re-raise the exception
                    
                    case "click":
                        print(f"Clicking element: selector='{css_selector}'")
                        target_element.click()
                        outcome = BrowserActionOutcome['SUCCESS']
                        after_action_delay = 500
                    case "focus":
                        print(f"Focusing on element: selector='{css_selector}'")
                        target_element.focus()
                        outcome = BrowserActionOutcome['SUCCESS']
                        after_action_delay = 500
                    case "goto":
                        print(f"Navigating to URL: {params['href']}")
                        self.page.evaluate(f"window.location.href = '{params['href']}'")
                        outcome = BrowserActionOutcome['SUCCESS']
                        after_action_delay = 1000  # Longer delay for page load                    
                    case "achieved":
                        print("Goal achieved!")
                        outcome = BrowserActionOutcome['GOAL_ACHIEVED']
                    
                    case "unreachable":
                        print("Goal unreachable.")
                        outcome = BrowserActionOutcome['GOAL_UNREACHABLE']
            except TimeoutError:
                print(f"Timeout error occurred while performing action: {function_name}")
                outcome = BrowserActionOutcome['TIMEOUT']

        # Always wait 100 milliseconds
        self.page.wait_for_timeout(after_action_delay)

        # If we caused a navigation, wait for load
        if (self.page.url != starting_url):
            self.page.wait_for_load_state("domcontentloaded")
    
        is_terminal_state = outcome in [BrowserActionOutcome['GOAL_ACHIEVED'], BrowserActionOutcome['GOAL_UNREACHABLE']]
        return BrowserActionResult(url=self.page.url, outcome=outcome, is_terminal_state=is_terminal_state)