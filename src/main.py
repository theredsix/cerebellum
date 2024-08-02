import json
import re
import tiktoken
import cssutils
import logging
import tiktoken
from openai import OpenAI
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup, Tag


# Suppress cssutils warnings and errors
cssutils.log.setLevel(logging.CRITICAL)


client = OpenAI()

# Define CSS properties that make elements non-visible
non_visible_styles = {
    'display': 'none',
    'visibility': 'hidden',
    'hidden': 'true',
    'aria-hidden': 'true',
}

# Function to check if an element is non-visible
def is_non_visible(element: Tag) -> bool:
    if element is None or not hasattr(element.attrs, 'get'):
        return False
    style_string = element.get('style', '')

    if style_string:
        # Parse the style string using cssutils
        style = cssutils.parseStyle(style_string)
        
        # Check for non-visible properties
        for prop, value in non_visible_styles.items():
            if style.getPropertyValue(prop) == value:
                # print('invisible element detected', element)
                return True

    return False

def remove_nonvisible_elements(soup: BeautifulSoup) -> BeautifulSoup:
    # Select all elements with style attribute
    tags_with_css = soup.select('[style]')
    
    for element in tags_with_css:
        if is_non_visible(element):
            element.decompose()
    
    # Remove elements with zero height or width
    zero_size_elements = soup.select('[style*="height: 0"], [style*="width: 0"]')
    for element in zero_size_elements:
        element.decompose()
    
    return soup

def remove_unused_css(soup: BeautifulSoup) -> BeautifulSoup:
    # Find all style tags
    style_tags = soup.find_all('style')
    
    for style_tag in style_tags:
        # Parse the CSS content
        stylesheet = cssutils.parseString(style_tag.string)
        
        # Keep track of used rules
        used_rules = []
        
        for rule in stylesheet:
            if rule.type == rule.STYLE_RULE:
                # Check if any element matches this rule
                try:
                    # Strip pseudo-classes from the selector
                    stripped_selector = re.sub(r'::?[a-zA-Z-]+(\([^)]*\))?', '', rule.selectorText)
                    if soup.select(stripped_selector):
                        used_rules.append(rule)
                except Exception as e:
                    print(f"Error processing selector '{rule.selectorText}': {e}")
                    # Keep the rule if we encounter an error
                    used_rules.append(rule)
        
        # If no rules are used, remove the entire style tag
        if not used_rules:
            style_tag.decompose()
        else:
            # Create a new stylesheet with only the used rules
            new_stylesheet = cssutils.css.CSSStyleSheet()
            for rule in used_rules:
                new_stylesheet.add(rule)
            
            # Replace the content of the style tag
            style_tag.string = new_stylesheet.cssText.decode('utf-8')
    
    return soup

def count_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-4o")
    return len(encoding.encode(text))

def remove_unnecessary_attributes(soup: BeautifulSoup) -> BeautifulSoup:
    allowed_attributes = ['aria-hidden', 'role', 'aria-label', 'aria-labelledby', 'aria-describedby', 'class', 'id']
    
    for tag in soup.find_all(True):  # Find all tags
        attrs_to_remove = [attr for attr in tag.attrs if attr not in allowed_attributes]
        for attr in attrs_to_remove:
            del tag[attr]
    
    return soup

def get_visible_html(page):
    # Get the page content
    content = page.content()
    
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove all script and meta tags
    for script in soup(["script", "meta"]):
        script.decompose()
    
    # Remove non-visible elements
    soup = remove_nonvisible_elements(soup)
    
    # Remove all style tags
    for style in soup(["style"]):
        style.decompose()

    remove_unnecessary_attributes(soup)

    # # Remove unused CSS
    # soup = remove_unused_css(soup)
    
    # Get the visible HTML
    visible_html = soup.prettify()

    # Count and print the number of tokens in visible_html
    token_count = count_tokens(visible_html)
    print(f"Number of tokens in visible_html: {token_count}")
    
    return visible_html


def get_next_action(prompt: str, visible_html: str) -> str:
    system_prompt = f'''
You are an expert developer in CSS and HTML with an excellent knowledge of jQuery and CSS selectors.
Given a web page in HTML format, decide the best action to take to complete the following goal. 
If you believe the goal cannot be achieved, call the "unreachable" function. 
If you believe the HTML shows that the goal has already been achieved, call the "achieved" function.

Goal: 
{prompt}
'''

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": visible_html},
        ],
        tools=[
             {
                "type": "function",
                "function": {
                    "name": "click_element",
                    "description": "Initial a mouse click on the intended HTML element",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "css_selector": {
                                "type": "string",
                                "description": "Specifies the CSS selector of the element to click. This string is a CSS selector that can be passed to jQuery",
                            }
                        },
                        "required": ["css_selector"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fill_input",
                    "description": "Fill in the input field with the specified text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "css_selector": {
                                "type": "string",
                                "description": "Specifies the CSS selector of the input element to fill. This string is a CSS selector that can be passed to jQuery",
                            },
                            "text": {
                                "type": "string",
                                "description": "The text that should be filled into the input element.",
                            },
                            "press_enter": {
                                "type": "boolean",
                                "description": "If true, the input will be filled and the enter key will be pressed. This is helpful for form or search submissions",
                            },
                        },
                        "required": ["css_selector", "text", "press_enter"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "achieved",
                    "description": "Call this function when the goal has been achieved.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "unreachable",
                    "description": "Call this function when if you believe the goal cannot be achieved.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ],
        tool_choice="required"
    )

    message = response.choices[0].message
    
    if message.tool_calls and isinstance(message.tool_calls, list) and len(message.tool_calls) > 0:
        return message.tool_calls
    else:
        return [{"type": "function", "function": {"name": "unreachable"}}]

def perform_action(page: Page, tool_calls: list):
    call = tool_calls.pop(0)
    
    if call is not None and call.type == "function":
        function_name = call.function.name
        arguments = call.function.arguments
        
        print(f"{function_name}({arguments})")

        match function_name:
            case "fill_input":
                params = json.loads(arguments)
                css_selector = params["css_selector"]
                text = params["text"]
                press_enter = params.get("press_enter", False)
                print(f"Filling input: selector='{css_selector}', text='{text}', press_enter={press_enter}")
                page.fill(css_selector, text)
                if press_enter:
                    page.press(css_selector, "Enter")
            
            case "click_element":
                params = json.loads(arguments)
                css_selector = params["css_selector"]
                print(f"Clicking element: selector='{css_selector}'")
                page.click(css_selector)
            
            case "achieved":
                print("Goal achieved!")
                return True
            
            case "unreachable":
                print("Goal unreachable.")
                return False
    
    print("No terminal action called, continuing...")
    return None  # Continue if no terminal action was called

def perform_browser_action(page: Page, goal: str):
    outcome = None
    while outcome is None:
        visible_html = get_visible_html(page)
        action = get_next_action(goal, visible_html)
        outcome = perform_action(page, action)
        while True:
            # Check for keyboard input
            input("Press enter to continue the browser...")
            break
    return outcome, page

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.amazon.com")
    goal = "find a usb c cable under 10 feet and add one it to my cart"

    perform_browser_action(page, goal)

    browser.close()



