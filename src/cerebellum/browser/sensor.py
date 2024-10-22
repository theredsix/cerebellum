import base64
import re
import cssutils
from html.parser import HTMLParser
from bs4 import BeautifulSoup, Comment, NavigableString, PageElement, Tag
from core import AbstractSensor
from cerebellum.browser.types import BrowserState
from playwright.sync_api import Page, TimeoutError
import logging
import cv2

cssutils.log.setLevel(logging.FATAL)

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

class BrowserSensor(AbstractSensor[BrowserState]):

    def __init__(self, page: Page):
        self.page = page

    @classmethod
    def find_clickable_elements(cls, soup: BeautifulSoup):
        """Find all clickable elements on the page."""
        return soup.select('a, button, [onclick], [role="button"], input[type="submit"], input[type="button"]')

    @classmethod
    def find_checkable_elements(cls, soup: BeautifulSoup):
        """Find all checkable elements on the page."""
        return soup.select('input[type="checkbox"], input[type="radio"]')
    
    @classmethod
    def find_selectable_elements(cls, soup: BeautifulSoup):
        """Find all selectable elements on the page and their options."""
        selectable_elements = {}
        for select_element in soup.find_all('select'):
            options = []
            for option in select_element.find_all('option'):
                value = option.get('value')
                text = option.text.strip()
                if value is None:
                    value = ""
                options.append({'value': value, 'text': text})
            selectable_elements[select_element] = options
        return selectable_elements

    @classmethod
    def find_fillable_elements(cls, soup: BeautifulSoup):
        """Find all fillable elements on the page."""
        fillable_elements = []
        for element in soup.find_all(['input', 'textarea']):
            if element.name == 'input':
                input_type = element.get('type', '').lower()
                if input_type not in ['submit', 'button', 'hidden', 'radio', 'checkbox']:
                    fillable_elements.append(element)
            else:  # textarea
                fillable_elements.append(element)
        
        # Add elements with contenteditable="true"
        fillable_elements.extend(soup.find_all(attrs={'contenteditable': 'true'}))
        
        return fillable_elements
    
    @classmethod
    def build_css_selector(cls, element: Tag, soup: BeautifulSoup) -> str:
        """
        Build a CSS selector for a given Tag.
        Prioritizes id over classnames.
        """
        selector_parts = []

        # Get the tag name
        tag_name = element.name
        selector_parts.append(tag_name)

        # Add href if the element is an 'a' tag and has an href attribute
        if tag_name == 'a' and element.get('href'):
            href = element.get('href')
            selector_parts.append(f'[href="{href}"]')

        # Add more attributes if selector isn't unique
        if cls.count_matching(soup, ''.join(selector_parts)) > 1:
            # Add aria-label if it exists
            if element.get('aria-label'):
                aria_label = element.get('aria-label')
                selector_parts.append(f'[aria-label="{aria_label}"]')
            elif element.get_text(strip=True):
                inner_text = element.get_text(strip=True)
                # Escape special characters in the inner text but not spaces
                escaped_text = re.escape(inner_text).replace("\\ ", " ")
                selector_parts.append(f':has-text("{escaped_text}")')

        # Add more attributes if selector isn't unique
        if cls.count_matching(soup, ''.join(selector_parts)) > 1:
            # Add id if it exists (highest priority)
            element_id = element.get('id')
            element_classes = element.get('class')
            if element_id:
                selector_parts.append(f"#{element_id}")
            elif element_classes: # Add classes if they exist
                # Validate if the class-based selector is unique
                class_selector = '.'.join(element_classes)
                selector_parts.append(f".{class_selector}")
            else: # If no classes or id, try to use a unique attribute
                for attr, value in element.attrs.items():
                    if attr not in ['class', 'style', 'href']:
                        selector_parts.append(f'[{attr}="{value}"]')
                        break
                    
        return ''.join(selector_parts)
    
    @classmethod
    def count_matching(cls, soup: BeautifulSoup, css_selector: str) -> int:
        """
        Count the number of elements that match a given CSS selector.
        If the :has-text selector is present, perform a case-insensitive inner-text match.
        """
        # Check if the selector includes :has-text
        if ':has-text(' in css_selector:
            # Extract the text to match
            start = css_selector.find(':has-text(') + len(':has-text(')
            end = css_selector.find(')', start)
            text_to_match = css_selector[start:end].strip('"').strip("'")
            
            # Remove the :has-text part from the selector for element matching
            base_selector = css_selector[:css_selector.find(':has-text(')]
            
            # Find all elements matching the base selector
            elements = soup.select(base_selector)
            
            # Filter elements by case-insensitive text match
            matching_elements = [
                element for element in elements
                if text_to_match.lower() in element.get_text(strip=True).lower()
            ]
            return len(matching_elements)
        else:
            # If no :has-text, simply count elements matching the selector
            return len(soup.select(css_selector))
    
    @classmethod
    def minify_html(cls, html_string):
        parser = SingleLineParser()
        parser.feed(html_string)
        single_line = parser.get_single_line_html()
        # Remove extra whitespace between tags
        return re.sub(r'>\s+<', '><', single_line)
    
    @classmethod
    def get_direct_descendants(cls, element: Tag) -> int:
        return [child for child in element.children if isinstance(child, Tag) or (isinstance(child, NavigableString) and child.strip())]
    
    @classmethod
    def collapse_single_child_to_parent(cls, soup: BeautifulSoup) -> BeautifulSoup:
        def dfs_collapse(element: PageElement):
            if not element or not hasattr(element, 'children') or not hasattr(element, 'name'):
                return
            
            saved_children = BrowserSensor.get_direct_descendants(element)

            # Check if this element has only one child
            if element.name in ['div', 'span'] and len(saved_children) == 1:
                if element.parent is not None and hasattr(element.parent, 'name') and element.parent.name != 'body':
                    element.unwrap()
                elif not isinstance(saved_children[0], NavigableString): #Case we're under body, we want to unwrap until we're one level above strings
                    element.unwrap()
            
            # Process children first (depth-first)
            for child in saved_children:
                dfs_collapse(child)          
            

        # Start the DFS from the root of the soup
        for element in list(soup.contents):
            dfs_collapse(element)

        return soup


    # Function to check if an element is non-visible
    @classmethod
    def is_non_visible(cls, element: Tag) -> bool:
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

    @classmethod
    def remove_nonvisible_elements(cls, soup: BeautifulSoup) -> BeautifulSoup:
        # Select all elements with style attribute
        tags_with_css = soup.select('[style]')
        
        for element in tags_with_css:
            if cls.is_non_visible(element):
                element.decompose()
        
        # Remove elements with zero height or width
        zero_size_elements = soup.select('[style*="height: 0"], [style*="width: 0"]')
        for element in zero_size_elements:
            element.decompose()
        
        return soup

    @classmethod
    def remove_unused_css(cls, soup: BeautifulSoup) -> BeautifulSoup:
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

    @classmethod
    def escape_id_and_classnames(cls, soup: BeautifulSoup) -> BeautifulSoup:
        chars_to_escape = r'~!@$%^&*()+=,.\/\';:\"?><[]\\{}|`#'
        escape_pattern = re.compile(f'([{re.escape(chars_to_escape)}])')

        for element in soup.find_all(attrs={'id': True}):
            element['id'] = escape_pattern.sub(r'\\\1', element['id'])

        for element in soup.find_all(attrs={'class': True}):
            element['class'] = [escape_pattern.sub(r'\\\1', cls) for cls in element['class']]

        return soup

    @classmethod
    def remove_unnecessary_attributes(cls, soup: BeautifulSoup) -> BeautifulSoup:
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
            'alt',
            'for',
            'checked',
            'is_checked'
        ]

        allowed_tags = ['label', 'svg', 'img', 'button', 'input', 'a', 'textarea', 'select', 'optgroup', 'option', 'select']

        for tag in soup.find_all(True):  # Find all tags
            if tag.name in allowed_tags or tag.attrs.get('draggable') or tag.attrs.get('contenteditable') or tag in cls.find_clickable_elements(soup):
                tag.attrs = {attr: value for attr, value in tag.attrs.items() if attr in allowed_attributes and value not in ('', None)}
            else:
                tag.attrs = {}

            # Check if is_checked is true and set checked attribute accordingly
            if tag.attrs.get('is_checked') == 'true':
                tag['checked'] = 'checked'
            # Remove the is_checked attribute as it's not a standard HTML attribute
            if 'is_checked' in tag.attrs:
                del tag['is_checked']

            if 'href' in tag.attrs:
                href = tag['href'].strip().lower()
                if href.startswith('javascript:') or href.startswith('#'):
                    del tag['href']
        
        return soup

    @classmethod
    def remove_empty_elements(cls, soup: BeautifulSoup) -> BeautifulSoup:
        def dfs_remove_empty(element: PageElement):
            if not element or not hasattr(element, 'contents') or not hasattr(element, 'name'):
                return

            # Process children first (depth-first)
            for child in list(element.contents):
                dfs_remove_empty(child)

            can_be_empty = [
                'head',
                'body',
                'a',
                'button',
                'input',
                'textarea',
                'select',
                'option'
            ]

            # Check if this element has only one child
            if element.name not in can_be_empty and len(cls.get_direct_descendants(element)) == 0:
                element.decompose()
            

        # Start the DFS from the root of the soup
        for element in list(soup.contents):
            dfs_remove_empty(element)

        return soup

    @classmethod
    def get_elements_in_viewport(cls, page: Page):
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
        return viewport_html

    @classmethod
    def empty_svg(cls, soup):
        for svg in soup.find_all('svg'):
            # Store attributes
            attrs = svg.attrs
            # Clear contents
            svg.clear()
            # Restore attributes
            svg.attrs = attrs
        return soup
    
    @classmethod
    def get_visible_html(cls, page: Page) -> str:
        visible_html = page.evaluate("""
        () => {
            function isNotVisible(el) {
                if (!el) return true;
                const style = window.getComputedStyle(el);
                return style.display === 'none' 
                    || style.visibility === 'hidden'
                    || style.opacity === '0'
            }

            function stripInvisible(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    return document.createTextNode(node.textContent);
                }
                if (node.nodeType !== Node.ELEMENT_NODE) {
                    return null;
                }
                if (isNotVisible(node)) {
                    return null;
                }
                const clone = node.cloneNode(false);
                                     
                // Check if the node is a radio button and add custom attribute if checked
                if (node.tagName === 'INPUT' && (node.type === 'radio' || node.type === 'checkbox')) {
                    if (node.checked) {
                        clone.setAttribute('is_checked', 'true');
                    }
                }
                                     
                for (const child of node.childNodes) {
                    const strippedChild = stripInvisible(child);
                    if (strippedChild) {
                        clone.appendChild(strippedChild);
                    }
                }
                return clone;
            }

            const strippedBody = stripInvisible(document.body);
            const returnText = strippedBody ? strippedBody.outerHTML : '';
            return returnText;
        }
        """)

        return visible_html
    
    def ensure_state_validity(self, last_state: BrowserState, change_threshold: float) -> bool:
        return BrowserSensor.did_screen_change(self.page, last_state.screenshot_full, change_threshold)

    @classmethod
    def did_screen_change(cls, page: Page, old_screenshot: str, threshold: float = 10) -> bool:
        print("old", old_screenshot)
        # Decode the base64 screenshots
        old_image_data = base64.b64decode(old_screenshot.encode('utf-8'))
        new_image_data = BrowserSensor.get_screenshot(page, True)

        # Decode the byte data to images using OpenCV
        old_image = cv2.imdecode(bytearray(old_image_data), cv2.IMREAD_COLOR)
        new_image = cv2.imdecode(bytearray(new_image_data), cv2.IMREAD_COLOR)

        # Ensure both images have the same size
        if old_image.shape != new_image.shape:
            raise ValueError("Screenshots do not have the same dimensions")

        # Calculate the absolute difference between the images
        diff_image = cv2.absdiff(old_image, new_image)

        # Count the number of different pixels
        diff_pixels = cv2.countNonZero(cv2.cvtColor(diff_image, cv2.COLOR_BGR2GRAY))

        # Calculate the percentage of changed pixels
        total_pixels = old_image.shape[0] * old_image.shape[1]
        change_percentage = (diff_pixels / total_pixels) * 100

        # Return True if more than 10% of the pixels have changed
        return change_percentage > threshold

    @classmethod
    def get_screenshot(cls, page: Page, full_page: bool = False) -> str:
        try_count = 1

        screenshot_bytes = None
        while try_count <= 3:
            try:
                page.wait_for_load_state('domcontentloaded')
                timeout = (10000+try_count*2000)
                screenshot_bytes = page.screenshot(
                    full_page=full_page, type='jpeg', quality=85, timeout=timeout)
                break
            except TimeoutError:
                print('Screenshot timed out on try', try_count, full_page)
            finally:
                try_count += 1

        if screenshot_bytes is not None:
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        else:
            print('Screenshot failed')
            return '' # Fail open

    def sense(self):
        page = self.page
        page.wait_for_load_state('domcontentloaded')

        screenshot_full=BrowserSensor.get_screenshot(page, full_page=True)
        screenshot_viewport=BrowserSensor.get_screenshot(page, full_page=False)

        # # Get the page content
        visible_html = BrowserSensor.get_visible_html(page)
        page_html = f'<html><head><title>{page.title()}</title></head>{visible_html}</html>'
        
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(page_html, 'html.parser')

        BrowserSensor.remove_nonvisible_elements(soup)

        BrowserSensor.empty_svg(soup)

        # BrowserSensor.collapse_single_child_to_parent(soup)

        # BrowserSensor.remove_empty_elements(soup)

        BrowserSensor.remove_unnecessary_attributes(soup)

        BrowserSensor.escape_id_and_classnames(soup)

        # # # Remove unused CSS
        # soup = remove_unused_css(soup)

        # # Remove all script and meta tags
        for tag in soup(["script", "meta", "link", "style"]):
            tag.decompose()
        
        # # Remove all HTML comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Get the visible HTML
        visible_html = soup.prettify()

        # Further compress HTML to one line to reduce token count
        visible_html = BrowserSensor.minify_html(visible_html)

        fillable_elements = BrowserSensor.find_fillable_elements(soup)
        clickable_elements = BrowserSensor.find_clickable_elements(soup)

        fillable_selectors = list(set([BrowserSensor.build_css_selector(x, soup) for x in fillable_elements]))
        clickable_selectors = list(set([BrowserSensor.build_css_selector(x, soup) for x in clickable_elements]))

        selectable_elements = BrowserSensor.find_selectable_elements(soup)
        checkable_elements = BrowserSensor.find_checkable_elements(soup)

        selectable_selectors = {}
        for select_element, options in selectable_elements.items():
            selector = BrowserSensor.build_css_selector(select_element, soup)
            selectable_selectors[selector] = [ x["value"] for x in options]

        checkable_selectors = list(set([BrowserSensor.build_css_selector(x, soup) for x in checkable_elements]))

        input_state = {}

        # Handle fillable elements
        for selector in fillable_selectors:
            element = self.page.locator(selector)
            if element.count() > 0:
                value = element.nth(0).input_value()
                input_state[selector] = value

        # Handle checkable elements
        for selector in checkable_selectors:
            element = self.page.locator(selector)
            if element.count() > 0:
                is_checked = element.nth(0).is_checked()
                input_state[selector] = 'checked' if is_checked else 'unchecked'

        # Handle selectable elements
        for selector in selectable_selectors:
            element = self.page.locator(selector)
            if element.count() > 0:
                selected_values = element.nth(0).evaluate("""
                    el => Array.from(el.selectedOptions)
                        .map(option => option.value)
                        .join(',')
                """)
                input_state[selector] = selected_values
        
        return BrowserState(
            html=visible_html,
            raw_html=BrowserSensor.minify_html(page.content()),
            screenshot_full=screenshot_full,
            screenshot_viewport=screenshot_viewport,
            url=self.page.url,
            fillable_selectors=fillable_selectors,
            clickable_selectors=clickable_selectors,
            selectable_selectors=selectable_selectors,
            checkable_selectors=checkable_selectors,
            input_state=input_state
        )

