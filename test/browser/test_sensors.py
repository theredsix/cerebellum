from bs4 import BeautifulSoup
from cerebellum.browser.sensor import BrowserSensor

def test_collapse_single_child_to_parent():
    
    # Read the pre-collapse HTML
    pre_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test for collapse_single_child_to_parent</title>
</head>
<body>
    <div>
        <div>
            <h1>This should collapse to only h1</h1>
        </div>
    </div>
    <div>
        <div>
            <span>This span should collapse to top</span>
        </div>
    </div>
    <span>
        <span>
            <span>This should collapse to a single span</span>
        </span>
    </span>
    <p>
        Other text
        <span>This should combine with the text</span>
    </p>
    <ul>
        <li>
            <li>
                <li>This should not collapse (ul can't have li as direct child)</li>
            </li>
        </li>
        <li>This should not collapse</li>
        <li>This should not collapse</li>
    </ul>
    <div>
        <p>This should not collapse</p>
        <span>This should become raw text in the div</span>
    </div>
    <button>
        <span>
            <span>This button content should collapse to raw text inside button</span>
        </span>
    </button>
    <div>
        <div>
            <div>
                <p>This p should collapse to a top</p>
            </div>
        </div>
    </div>
    <span>
        <span>
            <span>
                <div>This should collapse to a single div</div>
            </span>
        </span>
    </span>
</body>
</html>
'''
    # Read the expected post-collapse HTML
    
    expected_post_html = '''
<!DOCTYPE html>
<html lang="en">
 <head>
  <meta charset="utf-8"/>
  <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
  <title>
   Test for collapse_single_child_to_parent
  </title>
 </head>
 <body>
  <h1>
   This should collapse to only h1
  </h1>
  <span>
   This span should collapse to top
  </span>
  <span>
   This should collapse to a single span
  </span>
  <p>
   Other text
   This should combine with the text
  </p>
  <ul>
   <li>
    <li>
     <li>
      This should not collapse (ul can't have li as direct child)
     </li>
    </li>
   </li>
   <li>
    This should not collapse
   </li>
   <li>
    This should not collapse
   </li>
  </ul>
  <div>
   <p>
    This should not collapse
   </p>
   This should become raw text in the div
  </div>
  <button>
   This button content should collapse to raw text inside button
  </button>
  <p>
   This p should collapse to a top
  </p>
  <div>
   This should collapse to a single div
  </div>
 </body>
</html>
'''

    # Parse the pre-collapse HTML
    soup = BeautifulSoup(pre_html, 'html.parser')

    # Apply the collapse_single_child_to_parent method
    collapsed_soup = BrowserSensor.collapse_single_child_to_parent(soup)

    # Parse both the collapsed and expected HTML to normalize them
    actual = collapsed_soup.prettify()
    expected = BeautifulSoup(expected_post_html, 'html.parser').prettify()

    # Compare the collapsed HTML with the expected HTML
    assert actual == expected


def test_remove_empty_elements():
    pre_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test for remove_empty_elements</title>
</head>
<body>
    <div>
        <p>This paragraph should remain</p>
        <div></div>
        <span>   </span>
        <p> </p>
    </div>
    <div>
        <div>
            <span></span>
        </div>
    </div>
    <p>This paragraph should also remain</p>
    <div>
        <div>
            <p></p>
        </div>
        <span>Non-empty span</span>
    </div>
</body>
</html>
'''

    expected_post_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test for remove_empty_elements</title>
</head>
<body>
    <div>
        <p>This paragraph should remain</p>
    </div>
    <p>This paragraph should also remain</p>
    <div>
        <span>Non-empty span</span>
    </div>
</body>
</html>
'''

    # Parse the pre-removal HTML
    soup = BeautifulSoup(pre_html, 'html.parser')

    # Apply the remove_empty_elements method
    cleaned_soup = BrowserSensor.remove_empty_elements(soup)

    # Parse both the cleaned and expected HTML to normalize them
    actual = cleaned_soup.prettify()
    expected = BeautifulSoup(expected_post_html, 'html.parser').prettify()

    print(actual)
    print(expected)
    print(pre_html)

    # Compare the cleaned HTML with the expected HTML
    assert actual == expected
