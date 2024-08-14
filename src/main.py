import json
import re
import tiktoken
import cssutils
import logging
import tiktoken
import base64
from html.parser import HTMLParser
from datetime import datetime
from openai import OpenAI
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup, Tag, Comment


# Suppress cssutils warnings and errors
cssutils.log.setLevel(logging.CRITICAL)


client = OpenAI()



class SingleLineParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.in_style = False
        self.style_content = []

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            self.in_style = True
        attr_str = ' '.join(self.format_attribute(k, v) for k, v in attrs)
        self.result.append(f"<{tag}{' ' + attr_str if attr_str else ''}>")

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False
            # Compress and add the collected style content
            compressed_style = self.compress_css(''.join(self.style_content))
            self.result.append(compressed_style)
            self.style_content = []
        self.result.append(f"</{tag}>")

    def handle_data(self, data):
        if self.in_style:
            self.style_content.append(data)
        else:
            self.result.append(data.strip())

    def compress_css(self, css):
        try:
            sheet = cssutils.parseString(css)
            return sheet.cssText.decode('utf-8').replace('\n', ' ').replace('\r', '')
        except:
            # If parsing fails, fall back to basic compression
            return re.sub(r'\s+', ' ', css).strip()

    def get_single_line_html(self):
        return ''.join(self.result)

    def format_attribute(self, key, value):
        double_quote = '"'
        escaped_double_quote = '&quot;'
        if '"' in value and "'" not in value:
            return f"{key}='{value}'"
        elif '"' in value and "'" in value:
            return f'{key}="{value.replace(double_quote, escaped_double_quote)}"'
        else:
            return f'{key}="{value}"'

def compress_html(html_string):
    parser = SingleLineParser()
    parser.feed(html_string)
    single_line = parser.get_single_line_html()
    # Remove extra whitespace between tags
    return re.sub(r'>\s+<', '><', single_line)

def collapse_single_child_to_parent(soup: BeautifulSoup) -> BeautifulSoup:
    def dfs_collapse(element):
        if not element or not hasattr(element, 'contents'):
            return

        # Process children first (depth-first)
        for child in list(element.contents):
            dfs_collapse(child)

        # Check if this element has only one child
        if len(element.contents) == 1:
            child = element.contents[0]
            
            # Check if the child is a Tag (not a NavigableString) and has the same name as the parent
            if isinstance(child, Tag) and child.name == element.name:
                # Replace parent's contents with child's contents
                element.clear()
                element.extend(child.contents)

    # Start the DFS from the root of the soup
    for element in list(soup.contents):
        dfs_collapse(element)

    return soup


# Function to check if an element is non-visible
def is_non_visible(element: Tag) -> bool:
    # Define CSS properties that make elements non-visible
    non_visible_styles = {
        'display': 'none',
        'visibility': 'hidden',
        'hidden': 'true',
        'aria-hidden': 'true',
}

    if element is None or not hasattr(element.attrs, 'get'):
        return False
    style_string = element.get('style', '')

    if style_string:
        # Parse the style string using cssutils
        style = cssutils.parseStyle(style_string)
        
        # Check for non-visible properties
        for prop, value in non_visible_styles.items():
            property_value = style.getPropertyValue(prop)
            if property_value:
                # Remove any !important flag and trim whitespace
                cleaned_value = property_value.replace('!important', '').strip()
                if cleaned_value == value:
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
    allowed_attributes = [
        'role', 
        'aria-label', 
        'aria-labelledby', 
        'aria-describedby', 
        'class', 
        'id',
        'name',
        'title',
        'style',
        'draggable', 
        'contenteditable',
        'disabled',
        'form', 
        'disabled', 
        'multiple', 
        'required', 
        'size',
        'href',
        'type', 
        'value', 
        'placeholder',
        'alt'
    ]

    allowed_tags = ['img', 'input', 'a', 'textarea', 'select', 'optgroup', 'option']

    for tag in soup.find_all(True):  # Find all tags
        if tag.name in allowed_tags or tag.attrs.get('draggable') or tag.attrs.get('contenteditable'):
            tag.attrs = {attr: value for attr, value in tag.attrs.items() if attr in allowed_attributes and value not in ('', None)}
        else:
            tag.attrs = {}

        if 'href' in tag.attrs:
            href = tag['href'].strip().lower()
            if href.startswith('javascript:') or href.startswith('#'):
                del tag['href']
    
    return soup


def remove_empty_elements(soup: BeautifulSoup) -> BeautifulSoup:
    for element in soup.find_all(True):
        if not element.get_text(strip=True) and not element.find_all():
            element.decompose()
    return soup


def get_visible_html(page):
    # # Get the page content
    # content = page.content()

    elements_in_viewport = page.evaluate("""
    () => {
        const viewport = {
            top: window.pageYOffset,
            left: window.pageXOffset,
            right: window.pageXOffset + window.innerWidth,
            bottom: window.pageYOffset + window.innerHeight
        };

        function isPartiallyVisible(el) {
            if (el.nodeType === Node.TEXT_NODE) {
                el = el.parentElement;
            }
            const rect = el.getBoundingClientRect();
            return (
                rect.top < viewport.bottom &&
                rect.bottom > viewport.top &&
                rect.left < viewport.right &&
                rect.right > viewport.left
            );
        }

        function processNode(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                return isPartiallyVisible(node) ? document.createTextNode(node.textContent) : null;
            }
            
            if (node.nodeType !== Node.ELEMENT_NODE) {
                return null;
            }

            const clone = node.cloneNode(false);  // Shallow clone
            let hasVisibleContent = false;

            for (const child of node.childNodes) {
                const processedChild = processNode(child);
                if (processedChild) {
                    clone.appendChild(processedChild);
                    hasVisibleContent = true;
                }
            }

            // For inline elements, check visibility of parent
            if (!hasVisibleContent && getComputedStyle(node).display === 'inline') {
                hasVisibleContent = isPartiallyVisible(node);
            }

            return (hasVisibleContent || isPartiallyVisible(node)) ? clone : null;
        }

        const rootElement = document.body;
        const processedRoot = processNode(rootElement);
        
        return processedRoot ? processedRoot.outerHTML : '';
    }
    """)

    # Join the elements into a single HTML string and create a full HTML document
    viewport_html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{page.title()}</title></head>{''.join(elements_in_viewport)}</html>'''
    
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(viewport_html, 'html.parser')

    # Remove all HTML comments
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove all script and meta tags
    for script in soup(["script", "meta", "link"]):
        script.decompose()
    
    # Remove non-visible elements
    remove_nonvisible_elements(soup)

    collapse_single_child_to_parent(soup)

    # # Remove all style tags
    # for style in soup(["style"]):
    #     style.decompose()

    remove_unnecessary_attributes(soup)

    remove_empty_elements(soup)

    # # Remove unused CSS
    soup = remove_unused_css(soup)
    
    # Get the visible HTML
    visible_html = soup.prettify()

    # # Further compress HTML to one line to reduce token count
    visible_html = compress_html(visible_html)

    # Count and print the number of tokens in visible_html
    token_count = count_tokens(visible_html)
    print(f"Number of tokens in visible_html: {token_count}")

    # Write viewport_html to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"viewport_html_{timestamp}.html"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(visible_html)
    
    print(f"Viewport HTML saved to {filename}")
    
    return visible_html


def get_next_action(prompt: str, visible_html: str, viewport_screenshot: str, full_screenshot: str) -> str:
    system_prompt = f'''
You are an expert developer in CSS and HTML with an excellent knowledge of jQuery and CSS selectors.
Given a webpage's HTML and full + viewport screenshot, decide the best action to take to complete the following goal.

Key considerations:
* You are provided with a "viewport" view of the webpage and a full screenshot of the entire webpage. 
* The HTML provided is only of visible elements in the current viewport you may need to scroll the webpage to find the correct interactive elements
* If you believe the goal cannot be achieved, call the "unreachable" function. 
* If you believe the HTML shows that the goal has already been achieved, call the "achieved" function.
* Always explain your reasoning the "reasoning" argument to the function called.

Goal: 
{prompt}
'''

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {
                    "type": "text",
                    "text": visible_html
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{full_screenshot}",
                        "detail": "low"
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{viewport_screenshot}",
                        "detail": "high"
                    },
                }
            ]},
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
                            "reasoning": {
                                "type": "string",
                                "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                            },
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
                            "reasoning": {
                                "type": "string",
                                "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                            },
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
                    "name": "scroll_page",
                    "description": "Call this function to scroll the viewport, this will expose different HTML elements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reasoning": {
                                "type": "string",
                                "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                            },
                            "direction": {
                                "type": "string",
                                "description": "The direction for the scrolling action",
                                "enum": ["up", "down"],
                            },
                        },
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
                        "properties": {
                            "reasoning": {
                                "type": "string",
                                "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                            },
                        },
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
                        "properties": {
                            "reasoning": {
                                "type": "string",
                                "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                            },
                        },
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
    if len(tool_calls) > 0 and tool_calls[0] is not None and tool_calls[0].type == "function":
        call = tool_calls[0]
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

            case "scroll_page":
                params = json.loads(arguments)
                direction = params.get("direction", "down")
                print(f"Scrolling page: direction='{direction}'")
                
                # Get the viewport height
                viewport_height = page.evaluate("window.innerHeight")
                
                # Calculate scroll distance (3/4 of viewport)
                scroll_distance = int(viewport_height * 0.75)
                
                if direction == "up":
                    scroll_distance = -scroll_distance
                
                # Perform the scroll
                page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                
                # Wait for the scroll to complete
                page.wait_for_timeout(500)  # 500ms should be enough for most cases
            
            case "achieved":
                print("Goal achieved!")
                return True
            
            case "unreachable":
                print("Goal unreachable.")
                return False
    
    print("No terminal action called, continuing...")
    return None  # Continue if no terminal action was called

def save_training_data(page: Page, goal: str, actions: list, visible_html: str):
    data = {
        "url": page.url,
        "goal": goal,
        "action": {
            "name": actions[0].function.name,
            "arguments":  (json.loads(actions[0].function.arguments) if actions[0].function.arguments else None)
        },
        "visible_html": base64.b64encode(visible_html.encode()).decode()
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"browser_action_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Data saved to {filename}")

def inflate_html_from_training_data(filename: str):
    # Read the JSON file
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # Extract the base64 encoded HTML
    encoded_html = data.get('visible_html')
    
    if not encoded_html:
        print(f"No visible_html found in {filename}")
        return
    
    # Decode the HTML
    html = base64.b64decode(encoded_html).decode('utf-8')
    
    # Create a new filename for the HTML file
    html_filename = filename.replace('.json', '.html')
    
    # Write the HTML to a new file
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML extracted and saved to {html_filename}")

def grab_screenshot(page: Page) -> tuple[str, str]:
    # Capture full page screenshot as bytes
    full_screenshot_bytes = page.screenshot(type='jpeg', quality=90, full_page=True)
    
    # Capture viewport screenshot as bytes
    viewport_screenshot_bytes = page.screenshot(type='jpeg', quality=90, full_page=False)
    
    # Convert bytes to base64 encoded strings
    full_base64_image = base64.b64encode(full_screenshot_bytes).decode('utf-8')
    viewport_base64_image = base64.b64encode(viewport_screenshot_bytes).decode('utf-8')
    
    return full_base64_image, viewport_base64_image

def perform_browser_action(page: Page, goal: str):
    outcome = None
    while outcome is None:
        full_screenshot, viewport_screenshot = grab_screenshot(page)
        visible_html = get_visible_html(page)
        action = get_next_action(goal, visible_html, full_screenshot, viewport_screenshot)
        outcome = perform_action(page, action)
        # # Save data to JSON file
        save_training_data(page, goal, action, visible_html)

        wait_for_input()
    return outcome, page

def wait_for_input():
    while True:
        # Check for keyboard input
        input("Press enter to continue...")
        break

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    page.goto("https://www.google.com/")
    goal = "search for a usb c cable of 10 feet and it to cart"
    wait_for_input()

    perform_browser_action(page, goal)

    browser.close()


# inflate_html_from_training_data("browser_action_20240802_155237.json")

