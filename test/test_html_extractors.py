import difflib
import pytest
from bs4 import BeautifulSoup
from src.html_utils import VisibleHTMLExtractor

def test_collapse_single_child_to_parent():
    extractor = VisibleHTMLExtractor()

    # Read the pre-collapse HTML
    with open('test/html_samples/collapse_tag_pre.html', 'r') as f:
        pre_html = f.read()

    # Read the expected post-collapse HTML
    with open('test/html_samples/collapse_tag_post.html', 'r') as f:
        expected_post_html = f.read()

    # Parse the pre-collapse HTML
    soup = BeautifulSoup(pre_html, 'html.parser')

    # Apply the collapse_single_child_to_parent method
    collapsed_soup = extractor.collapse_single_child_to_parent(soup)

    # Parse both the collapsed and expected HTML to normalize them
    actual = collapsed_soup.prettify()
    expected = BeautifulSoup(expected_post_html, 'html.parser').prettify()

    print(actual)
    print(expected)

    # Compare the collapsed HTML with the expected HTML
    assert actual == expected
