
from ast import List
import html
from bs4 import BeautifulSoup
from core import AbstractSessionRecorder, ActionT, RecordedAction, ResultT, StateT
from playwright import Page


class PageActionRecorder(AbstractSessionRecorder):
    page: Page

    def __init__(self, display_page: Page):
        self.page = display_page

    def display_state(self, action: RecordedAction) -> None:
        # Parse and pretty print the HTML content        
        soup = BeautifulSoup(action.state.html, 'html.parser')
        pretty_html = html.escape(soup.prettify())
        
        # Create an HTML document with viewport screenshot, full screenshot, pretty-printed HTML, action, and result
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser Session State - Step {action.state.url}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h2 {{ color: #333; }}
        img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin-bottom: 20px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f5f5f5; padding: 15px; border: 1px solid #ddd; }}
        .action-result {{ background-color: #e6f3ff; padding: 15px; border: 1px solid #b8d4ff; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h2>Action</h2>
    <div class="action-result">
        <p><strong>Intent:</strong> {action.action.reason}</p>
        <p><strong>Function:</strong> {action.action.function}</p>
        <p><strong>Arguments:</strong> {'<br>'.join([f"{k}: {v}" for k, v in action.action.args.items()])}</p>
    </div>

    <h2>Result</h2>
    <div class="action-result">
        <p><strong>URL:</strong> {action.result.url}</p>
        <p><strong>Outcome:</strong> {action.result.outcome}</p>
    </div>

    <h2>Viewport Screenshot</h2>
    <img src="data:image/png;base64,{action.state.screenshot_viewport}" alt="Viewport Screenshot">
    
    <h2>Full Page Screenshot</h2>
    <img src="data:image/png;base64,{action.state.screenshot_full}" alt="Full Page Screenshot">
    
    <h2>Page HTML</h2>
    <pre>{pretty_html}</pre>
</body>
</html>
        """
        
        # Set the content of the page to our created HTML
        self.page.set_content(html_content)

    def record(self, goal: str,
              past_actions: List[RecordedAction[StateT, ActionT, ResultT]],
               step: int | None = None) -> bool:
        self.display_state(past_actions[-1])
