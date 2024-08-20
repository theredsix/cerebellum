import re
import cssutils
from html.parser import HTMLParser
from bs4 import BeautifulSoup, NavigableString, PageElement, Tag
from src.core_abstractions import AbstractSensor
from src.limb.browser.types import BrowserState
from playwright.sync_api import Page

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
    page: Page

    def __init__(self, page: Page):
        self.page = page

    def minify_html(self, html_string):
        parser = SingleLineParser()
        parser.feed(html_string)
        single_line = parser.get_single_line_html()
        # Remove extra whitespace between tags
        return re.sub(r'>\s+<', '><', single_line)
    
    def get_direct_descendants(self, element: Tag) -> int:
        return [child for child in element.children if isinstance(child, Tag) or (isinstance(child, NavigableString) and child.strip())]
    
    def collapse_single_child_to_parent(self, soup: BeautifulSoup) -> BeautifulSoup:
        def dfs_collapse(element: PageElement):
            if not element or not hasattr(element, 'children') or not hasattr(element, 'name'):
                return
            
            saved_children = self.get_direct_descendants(element)

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
    def is_non_visible(self, element: Tag) -> bool:
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

    def remove_nonvisible_elements(self, soup: BeautifulSoup) -> BeautifulSoup:
        # Select all elements with style attribute
        tags_with_css = soup.select('[style]')
        
        for element in tags_with_css:
            if self.is_non_visible(element):
                element.decompose()
        
        # Remove elements with zero height or width
        zero_size_elements = soup.select('[style*="height: 0"], [style*="width: 0"]')
        for element in zero_size_elements:
            element.decompose()
        
        return soup

    def remove_unused_css(self, soup: BeautifulSoup) -> BeautifulSoup:
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

    def remove_unnecessary_attributes(self, soup: BeautifulSoup) -> BeautifulSoup:
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

        allowed_tags = ['svg', 'img', 'button', 'input', 'a', 'textarea', 'select', 'optgroup', 'option']

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


    def remove_empty_elements(self, soup: BeautifulSoup) -> BeautifulSoup:
        def dfs_remove_empty(element: PageElement):
            if not element or not hasattr(element, 'contents') or not hasattr(element, 'name'):
                return

            # Process children first (depth-first)
            for child in list(element.contents):
                dfs_remove_empty(child)          

            # Check if this element has only one child
            if element.name not in ['head', 'body'] and len(self.get_direct_descendants(element)) == 0:
                element.decompose()
            

        # Start the DFS from the root of the soup
        for element in list(soup.contents):
            dfs_remove_empty(element)

        return soup

    def get_elements_in_viewport(self, page: Page):
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

    def empty_svg(self, soup):
        for svg in soup.find_all('svg'):
            # Store attributes
            attrs = svg.attrs
            # Clear contents
            svg.clear()
            # Restore attributes
            svg.attrs = attrs
        return soup

    def sense(self, page: Page):
        # # Get the page content
        content = page.content()
        
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        self.remove_nonvisible_elements(soup)

        self.remove_unnecessary_attributes(soup)

        self.remove_empty_elements(soup)

        self.collapse_single_child_to_parent(soup)

        # # # Remove unused CSS
        # soup = remove_unused_css(soup)

        self.empty_svg(soup)

        # # Remove all script and meta tags
        for tag in soup(["script", "meta", "link", "style"]):
            tag.decompose()
        
        # # Remove all HTML comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Get the visible HTML
        visible_html = soup.prettify()

        # Further compress HTML to one line to reduce token count
        visible_html = self.minify_html(visible_html)
        
        return BrowserState(
            html=visible_html,
            raw_html=self.minify_html(content),
            screenshot_full=self.page.screenshot(full_page=True),
            screenshot_viewport=self.page.screenshot(),
            url=self.page.url
        )

