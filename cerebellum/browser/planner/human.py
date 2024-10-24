import copy
import html
import json
import random
import string
from typing import Any, Dict, List
from bs4 import BeautifulSoup
from playwright.sync_api import Page
from core import AbstractPlanner, RecordedAction, SupervisorPlanner

import requests
from cerebellum.browser.types import BrowserAction, BrowserActionOutcome, BrowserActionResult, BrowserState
from cerebellum.browser.planner.llm import AbstractLLMBrowserPlanner

class HumanBrowserPlanner(SupervisorPlanner[BrowserState, BrowserAction, BrowserActionResult]):
    def __init__(self, base_planner: AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult], display_page: Page):
        super().__init__(
            base_planner=base_planner
        )
        self.display_page = display_page
    
    def review_action(self, recommended_action: BrowserAction, goal: str, current_state: BrowserState, 
        past_actions: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]) -> BrowserAction:

        soup = BeautifulSoup(current_state.html, 'html.parser')
        pretty_html = html.escape(soup.prettify())
        
        # Create a simple HTML interface for displaying and overwriting recommended actions
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Action Review</title>
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                #recommended-action, #custom-action {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }}
                label {{ display: block; margin-top: 10px; }}
                input[type="text"], select {{ width: 100%; padding: 5px; margin-top: 5px; }}
                button {{ background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; margin-right: 10px; display: block; }}
            </style>
        </head>
        <body>
            <h1>Action Review</h1>
            <div id="recommended-action">
                <h2>Recommended Action</h2>
                <p id="rec-prior-steps">Prior Steps: {html.escape(recommended_action.prior_steps)}</p>
                <p id="rec-current-state">Current State: {html.escape(recommended_action.current_state)}</p>
                <p id="rec-top-5-actions">Top 5 Actions:</p>
                {' '.join([f'<p>Action {i+1}: {html.escape(action)}</p>' for i, action in enumerate(recommended_action.top_5_actions)])}
                <p id="rec-action-analysis">Action Analysis: {html.escape(recommended_action.action_analysis)}</p>
                <p id="rec-function">Function: {html.escape(recommended_action.function)}</p>
                <p id="rec-css-selector">CSS Selector: {html.escape(recommended_action.args.get('css_selector', 'N/A'))}</p>
                <p id="rec-text">Text: {html.escape(recommended_action.args.get('text', 'N/A'))}</p>
                <button onclick="continueRecommendedAction()">Continue with Recommended Action</button>
            </div>
            <div id="custom-action">
                <h2>Custom Action</h2>
                <label for="function">Function:</label>
                <select id="function">
                    <option value="click" {('selected' if recommended_action.function == 'click' else '')}>Click</option>
                    <option value="fill" {('selected' if recommended_action.function == 'fill' else '')}>Fill</option>
                    <option value="focus" {('selected' if recommended_action.function == 'focus' else '')}>Focus</option>
                    <option value="achieved" {('selected' if recommended_action.function == 'achieved' else '')}>Achieved</option>
                    <option value="unreachable" {('selected' if recommended_action.function == 'unreachable' else '')}>Unreachable</option>
                </select>
                <label for="prior-steps">Prior Steps:</label>
                <input type="text" id="prior-steps" value="{html.escape(recommended_action.prior_steps)}">
                <label for="current-state">Current State:</label>
                <input type="text" id="current-state" value="{html.escape(recommended_action.current_state)}">
                <label for="top-5-actions">Top 5 Actions:</label>
                {' '.join([f'<input type="text" id="top-5-action-{i+1}" value="{html.escape(action)}">' for i, action in enumerate(recommended_action.top_5_actions)])}
                <label for="action-analysis">Action Analysis:</label>
                <input type="text" id="action-analysis" value="{html.escape(recommended_action.action_analysis)}">
                <label for="css-selector">CSS Selector:</label>
                <input type="text" id="css-selector" value="{html.escape(recommended_action.args.get('css_selector', ''))}">
                <label for="text">Text (for fill action):</label>
                <input type="text" id="text" value="{html.escape(recommended_action.args.get('text', ''))}">
                <label for="press-enter">Press Enter (for fill action):</label>
                <input type="checkbox" id="press-enter" {('checked' if recommended_action.args.get('press_enter', False) else '')}>
                <button onclick="submitCustomAction()">Submit Custom Action</button>
            </div>
            <h2>Clickable Elements</h2>
            <ul>
                {' '.join([f'<li>{html.escape(selector)}</li>' for selector in current_state.clickable_selectors])}
            </ul>
            
            <h2>Fillable Elements</h2>
            <ul>
                {' '.join([f'<li>{html.escape(selector)}</li>' for selector in current_state.fillable_selectors])}
            </ul>
            
            <h2>Checkable Elements</h2>
            <ul>
                {' '.join([f'<li>{html.escape(selector)}</li>' for selector in current_state.checkable_selectors])}
            </ul>
            
            <h2>Selectable Elements</h2>
            <ul>
                {' '.join([f'<li>{html.escape(selector)}: {", ".join(html.escape(option) for option in options)}</li>' for selector, options in current_state.selectable_selectors.items()])}
            </ul>
            
            <h2>Input State</h2>
            <ul>
                {' '.join([f'<li>{html.escape(selector)}: {html.escape(str(value))}</li>' for selector, value in current_state.input_state.items()])}
            </ul>
            <h2>Viewport Screenshot</h2>
            <img src="data:image/png;base64,{current_state.screenshot_viewport}" alt="Viewport Screenshot">
            
            <h2>Full Page Screenshot</h2>
            <img src="data:image/png;base64,{current_state.screenshot_full}" alt="Full Page Screenshot">
            
            <h2>Page HTML</h2>
            <pre>{pretty_html}</pre>
            <script>
                window.actionSubmitted = false;
                function submitCustomAction() {{
                    var action = {{
                        function: $('#function').val(),
                        args: {{
                            css_selector: $('#css-selector').val(),
                            text: $('#text').val(),
                            press_enter: $('#press-enter').is(':checked')
                        }},
                        prior_steps: $('#prior-steps').val(),
                        current_state: $('#current-state').val(),
                        top_5_actions: [
                            $('#top-5-action-1').val(),
                            $('#top-5-action-2').val(),
                            $('#top-5-action-3').val(),
                            $('#top-5-action-4').val(),
                            $('#top-5-action-5').val()
                        ],
                        action_analysis: $('#action-analysis').val(),
                    }};
                    // Send action back to Python
                    window.finalAction = JSON.stringify(action);
                    window.actionSubmitted = true;
                }}

                function continueRecommendedAction() {{
                    var action = {{
                        function: {json.dumps(recommended_action.function)},
                        args: {json.dumps(recommended_action.args)},
                        prior_steps: {json.dumps(recommended_action.prior_steps)},
                        current_state: {json.dumps(recommended_action.current_state)},
                        top_5_actions: {json.dumps(recommended_action.top_5_actions)},
                        action_analysis: {json.dumps(recommended_action.action_analysis)}
                    }};
                    // Send recommended action back to Python
                    window.finalAction = JSON.stringify(action);
                    window.actionSubmitted = true;
                }}
            </script>
        </body>
        </html>
        """

        # Update the display page with the HTML content
        self.display_page.set_content(html_content)

        # Wait for user input
        self.display_page.wait_for_function("() => window.actionSubmitted", timeout=0)
        action = self.display_page.evaluate("() => window.finalAction")

        print(action)
        # Parse the action
        parsed_action = json.loads(action)
        return BrowserAction(
            function=parsed_action['function'],
            args=parsed_action['args'],
            prior_steps=parsed_action['prior_steps'],
            current_state=parsed_action['current_state'],
            top_5_actions=parsed_action['top_5_actions'],
            action_analysis=parsed_action['action_analysis']
        )
