
from bs4 import BeautifulSoup


class PageActionRecorder(AbstractSessionRecorder):
    page: Page

    def __init__(self, page: Page):
        self.page = page

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

    def record(self, session: AbstractBrowserSession) -> None:
        self.display_state(session.actions[-1])

    def record_step(self, session: AbstractBrowserSession, step: int) -> None:
        # Display the state for the given step
        action = session.actions[step - 1]
        self.display_state(action)

    def recover(self) -> (str, List[RecordedAction]):
        # This method is not implemented for this recorder
        raise NotImplementedError("The recover method is not supported for this recorder.")