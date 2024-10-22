from cerebellum.browser.limb import BrowserLimb


def test_strip_unnecessary_escaped_char():
    # Test cases
    test_cases = [
        (r'input[name=\"user\[name\]\"]', 'input[name="user\[name\]"]'),
        (r'div.class\:name', 'div.class\:name'),
        (r'input[type=\"text\"]', 'input[type="text"]'),
        (r'a[href=\"https://example.com\"]', 'a[href="https://example.com"]'),
        (r'button:contains(\"Submit\")', 'button:contains("Submit")'),
        (r'p.class1\.class2', 'p.class1\.class2'),
        (r'span[data-value=\"1\,2\,3\"]', 'span[data-value="1\,2\,3"]'),
        (r'a[title=\"Quote: \"Hello\"\"]', 'a[title="Quote: \\"Hello\\""]'),
        (r'div#my\-id', 'div#my-id'),
        (r'div.class\@name', 'div.class@name'),
    ]

    for input_selector, expected_output in test_cases:
        result = BrowserLimb.strip_unnecessary_escaped_char(input_selector)
        assert result == expected_output, f"Failed for input '{input_selector}'. Expected '{expected_output}', but got '{result}'"

    print("All test cases passed for strip_unnecessary_escaped_char")
