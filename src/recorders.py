import html
from typing import List
import json
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import Page
from src.core_abstractions import AbstractBrowserSession, AbstractSessionRecorder, ActionOutcome, ActionResult, PageAction, PageState, RecordedAction

class FileSessionRecorder(AbstractSessionRecorder):
    file_path: str

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def record(self, session: AbstractBrowserSession) -> None:
        # Create a new zip file
        with zipfile.ZipFile(self.file_path, 'w'):
            pass  # Just create an empty zip file

        # Record each step
        for step in range(len(session.actions)):
            self.record_step(session, step)

    def record_step(self, session: AbstractBrowserSession, step: int) -> None:
        with zipfile.ZipFile(self.file_path, 'a') as zip_file:
            if step == 0:
                # Save the goal if it's the first step
                goal_data = {"goal": session.goal}
                zip_file.writestr('goal.json', json.dumps(goal_data, indent=2))
            
            # Save the specific action
            action = session.actions[step]
            action_data = {
                "state": {
                    "html": action.state.html,
                    "screenshot_full": action.state.screenshot_full,
                    "screenshot_viewport": action.state.screenshot_viewport,
                    "url": action.state.url
                },
                "action": {
                    "function": action.action.function,
                    "args": action.action.args,
                    "reason": action.action.reason
                },
                "result": {
                    "url": action.result.url,
                    "outcome": action.result.outcome.value
                }
            }
            zip_file.writestr(f'action{step}.json', json.dumps(action_data, indent=2))

    def recover(self) -> tuple[str, List[RecordedAction]]:
        goal = ""
        actions = []

        with zipfile.ZipFile(self.file_path, 'r') as zip_file:
            # Read the goal
            with zip_file.open('goal.json') as goal_file:
                goal_data = json.load(goal_file)
                goal = goal_data['goal']

            # Read all action files
            action_files = sorted([f for f in zip_file.namelist() if f.startswith('action') and f.endswith('.json')],
                                  key=lambda x: int(x[6:-5]))  # Sort by action number

            for action_file in action_files:
                with zip_file.open(action_file) as file:
                    action_data = json.load(file)
                    
                    state = PageState(
                        html=action_data['state']['html'],
                        screenshot_full=action_data['state']['screenshot_full'],
                        screenshot_viewport=action_data['state']['screenshot_viewport'],
                        url=action_data['state']['url']
                    )
                    
                    action = PageAction(
                        function=action_data['action']['function'],
                        args=action_data['action']['args'],
                        reason=action_data['action']['reason']
                    )
                    
                    result = ActionResult(
                        url=action_data['result']['url'],
                        outcome=ActionOutcome(action_data['result']['outcome'])
                    )
                    
                    recorded_action = RecordedAction(state, action, result)
                    actions.append(recorded_action)

        return goal, actions
    

class PausingRecorder(AbstractSessionRecorder):

    def wait_for_input(self):
        input("Press Enter to continue...")

    def record_step(self, session: AbstractBrowserSession, step: int):
        self.wait_for_input()

    def record(self, session: AbstractBrowserSession) -> None:
        self.wait_for_input()

    def recover(self) -> (str, List[RecordedAction]):
        # This method is not implemented for this recorder
        raise NotImplementedError("The recover method is not supported for this recorder.")

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