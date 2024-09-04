import base64
import re
import cssutils
from html.parser import HTMLParser
from bs4 import BeautifulSoup, Comment, NavigableString, PageElement, Tag
from cerebellum.core_abstractions import AbstractSensor
from cerebellum.limb.browser.types import BrowserState
from playwright.sync_api import Page, TimeoutError
import logging

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
    def find_fillable_elements(cls, soup: BeautifulSoup):
        """Find all fillable elements on the page."""
        fillable_elements = []
        for element in soup.find_all(['input', 'textarea']):
            if element.name == 'input':
                input_type = element.get('type', '').lower()
                if input_type not in ['submit', 'button', 'hidden']:
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

        # Add id if it exists (highest priority)
        element_id = element.get('id')
        if element_id:
            selector_parts.append(f"#{element_id}")
            return ''.join(selector_parts)  # Return immediately if id is found

        # Add classes if they exist
        # Validate if the class-based selector is unique
        element_classes = element.get('class')
        if element_classes:
            class_selector = '.'.join(element_classes)
            selector_parts.append(f".{class_selector}")
            matching_elements = soup.select(f"{tag_name}.{class_selector}")
            
            # If the selector is not unique, add a :contains() pseudo-class
            if len(matching_elements) > 1:
                inner_text = element.get_text(strip=True)
                if inner_text:
                    # Escape special characters in the inner text
                    escaped_text = re.escape(inner_text)
                    selector_parts.append(f':contains("{escaped_text}")')
                else:
                    # If no inner text, try to use a unique attribute
                    for attr, value in element.attrs.items():
                        if attr not in ['class', 'style']:
                            selector_parts.append(f'[{attr}="{value}"]')
                            break                
        
        # If no classes or id, try to use a unique attribute
        if not element_id and not element_classes:
            for attr, value in element.attrs.items():
                if attr not in ['class', 'style']:
                    selector_parts.append(f'[{attr}="{value}"]')
                    break

        return ''.join(selector_parts)
    
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
            'checked'
        ]

        allowed_tags = ['label', 'svg', 'img', 'button', 'input', 'a', 'textarea', 'select', 'optgroup', 'option']

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

        # BrowserSensor.remove_nonvisible_elements(soup)

        BrowserSensor.collapse_single_child_to_parent(soup)

        BrowserSensor.remove_empty_elements(soup)

        BrowserSensor.empty_svg(soup)
        
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
        
        return BrowserState(
            html=visible_html,
            raw_html=BrowserSensor.minify_html(page.content()),
            screenshot_full=screenshot_full,
            screenshot_viewport=screenshot_viewport,
            url=self.page.url,
            fillable_selectors=fillable_selectors,
            clickable_selectors=clickable_selectors,
        )
