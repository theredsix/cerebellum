import html
import json
from bs4 import BeautifulSoup
import requests
import json
from playwright.sync_api import Page
from typing import List, Dict, Any
from cerebellum.core_abstractions import AbstractPlanner, SupervisorPlanner, RecordedAction
from cerebellum.limb.browser.types import BrowserAction, BrowserActionOutcome, BrowserActionResult, BrowserState

tools = [
             {
                "name": "click",
                "description": "Initial a mouse click on the intended HTML element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": '''A CSS selector targeting the element to click, the target element MUST match a css selector from 'Clickable Elements'. use the following priority order for CSS selectors:
  1. ID-based selectors (e.g., 'tag#id') - ALWAYS prefer these if available
  2. Unique class-based selectors
  3. Attribute selectors
  4. Combination of tag and class/attribute''',
                        }
                    },
                    "required": ["reasoning", "css_selector"],
                },
            },
            {
                "name": "fill",
                "description": 'Fill in the <input>, <textarea>, or [contenteditable] element with the specified text. Do not target input[type="hidden"] elements',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": '''A CSS selector targeting the element to fill, the target element MUST match a css selector from 'Fillable Elements'. use the following priority order for CSS selectors:
  1. ID-based selectors (e.g., 'tag#id') - ALWAYS prefer these if available
  2. Unique class-based selectors
  3. Attribute selectors
  4. Combination of tag and class/attribute''',
                        },
                        "text": {
                            "type": "string",
                            "description": "The text that should be filled into the input element.",
                        },
                        "press_enter": {
                            "type": "boolean",
                            "description": "If true, the enter key will be pressed after the input is filled. This is helpful for form or search submissions",
                        },
                    },
                    "required": ["reasoning", "css_selector", "text", "press_enter"],
                },
            },
            {
                "name": "focus",
                "description": "Scroll the viewport to an element, only use this function to display a part of the page to the user. Do not use if you intent to interact with an offscreen element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": '''A CSS selector targeting the element to focus. Use the following priority order for CSS selectors:
  1. ID-based selectors (e.g., 'tag#id') - ALWAYS prefer these if available
  2. Unique class-based selectors
  3. Attribute selectors
  4. Combination of tag and class/attribute''',
                        },
                    },
                    "required": ["reasoning", "css_selector"],
                },
            },
            {
                "name": "achieved",
                "description": "Call this function when the goal has been achieved.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                    },
                    "required": ["reasoning"],
                },
            },
            {
                "name": "unreachable",
                "description": "Call this function when if you believe the goal cannot be achieved.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                    },
                    "required": ["reasoning"],
                },
            },
        ]

tool_config = {
  "function_calling_config": {
    "mode": "ANY",
    "allowed_function_names": ["click", "fill", "focus", "achieved", "unreachable"]
  },
}

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
                <p id="rec-function">Function: {html.escape(recommended_action.function)}</p>
                <p id="rec-reasoning">Reasoning: {html.escape(recommended_action.reason)}</p>
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
                <label for="reasoning">Reasoning:</label>
                <input type="text" id="reasoning" value="{html.escape(recommended_action.reason)}">
                <label for="css-selector">CSS Selector:</label>
                <input type="text" id="css-selector" value="{html.escape(recommended_action.args.get('css_selector', ''))}">
                <label for="text">Text (for fill action):</label>
                <input type="text" id="text" value="{html.escape(recommended_action.args.get('text', ''))}">
                <label for="press-enter">Press Enter (for fill action):</label>
                <input type="checkbox" id="press-enter" {('checked' if recommended_action.args.get('press_enter', False) else '')}>
                <button onclick="submitCustomAction()">Submit Custom Action</button>
            </div>
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
                        reason: $('#reasoning').val(),
                    }};
                    // Send action back to Python
                    window.finalAction = JSON.stringify(action);
                    window.actionSubmitted = true;
                }}

                function continueRecommendedAction() {{
                    var action = {{
                        function: {json.dumps(recommended_action.function)},
                        args: {json.dumps(recommended_action.args)},
                        reason: {json.dumps(recommended_action.reason)}
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
            reason=parsed_action['reason']
        )

class GeminiBrowserPlanner(AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult]):

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro-latest"):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = 0


    def generate_content(self, system_instructions: str, contents: List[Dict[str, Any]], tools: List[Dict[str, Any]], temperature=0) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "system_instruction": {
                "parts": {
                    "text": system_instructions
                }
            },
            "contents": contents,
            "tools": [
                {
                    "function_declarations": tools
                }
            ],
            "tool_config": tool_config,
            "generation_config": {
                "temperature": temperature
            }
        }
        
        print('Calling Gemini')
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        print(response)

        return response.json()


    def format_actions_into_chats(self, session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]):
        chat_messages = []
        for past_action in session_history:
            chat_messages.append({
                "role": "user",
                "parts": [
                    { "inline_data": 
                        {
                            "mime_type":"image/jpeg",
                            "data": past_action.state.screenshot_viewport
                        }
                    },
                    {"text": f"Viewport screenshot"},
                    {"text": f"URL: {past_action.state.url}"},
                ]
            })
            # Add the action as a model message
            arg_dict = past_action.action.args
            arg_dict['reasoning'] = past_action.action.reason
            function_call_msg = {
                "role": "model",
                "parts": [
                    {
                        "functionCall": {
                            "name": past_action.action.function,
                            "args": arg_dict
                        }
                    }
                ]
            }
            chat_messages.append(function_call_msg)
            
            # Add the result as a function message
            function_response_msg = {
                "role": "function",
                "parts": [{
                    "functionResponse": {
                        "name": past_action.action.function,
                        "response": {
                            "name": past_action.action.function,
                            "content": {
                                "outcome": past_action.result.outcome,
                                "url": past_action.result.url
                            }
                        }
                    }
                }]
            }
            chat_messages.append(function_response_msg)
        
        return chat_messages
    

    def format_state_into_chat(self, state: BrowserState, goal: str):
        chat_message = {
            "role": "user",
            "parts": [
            ]
        }

        if state.screenshot_full:
            chat_message["parts"].extend([
                { "inline_data": 
                    {
                        "mime_type":"image/jpeg",
                        "data": state.screenshot_full
                    }
                },
                {"text": f"Full webpage screenshot"}
            ])

        if state.screenshot_viewport and state.screenshot_viewport != state.screenshot_full:
            chat_message["parts"].extend([
                { "inline_data": 
                    {
                        "mime_type":"image/jpeg",
                        "data": state.screenshot_viewport
                    }
                },
                {"text": f"Viewport screenshot"},
            ])

        clickable_selectors = '\n'.join(state.clickable_selectors)
        fillable_selectors = '\n'.join(state.fillable_selectors)
        chat_message["parts"].extend([
            {"text": f"URL: {state.url}"},
            {"text": f"HTML:\n{state.html}"},
            {"text": f"Clickable Elements\n###\n{clickable_selectors}\n###"},
            {"text": f"Fillable Elements\n###\n{fillable_selectors}\n###"},
            # {"text": f"Goal:\n{goal}"},
        ])

        return chat_message
    
    def get_system_prompt(self, goal: str):
        system_prompt = f'''
You are an expert developer in CSS and HTML with an excellent knowledge of jQuery and CSS selectors.
Given a webpage's HTML and full + viewport screenshot, decide the best action to take to complete the following goal.

Key considerations:
* Only consider the goal achieved if and only if the current state and function call history achieves ALL parts of the goal
* A goal is not achieved if you believe there is one or more additional action necessary (i.e clicking, filling, submitting)
* Verify search results align with the goal; don't assume accuracy
* You are provided with a "viewport" view of the webpage and a full screenshot of the entire webpage.
* When selecting elements, use the following priority order for CSS selectors:
  1. ID-based selectors (e.g., 'tag#id') - ALWAYS prefer these if available
  2. Unique class-based selectors
  3. Attribute selectors
  4. Combination of tag and class/attribute
* Target element argument of click() functionCall must match a css selector from 'Clickable Elements'
* Target element argument of fill() functionCall must match a css selector from 'Fillable Elements'
* If you believe the goal cannot be achieved, call the "unreachable" function. 
* If you believe the HTML and viewport screenshot shows that the goal has already been achieved without any further action from the user or you, call the "achieved" function.
* Always explain your reasoning the "reasoning" argument to the function called.
* Always press ENTER after filling the last or only input field.
* Solve captcha pages if they come up.

Goal: 
{goal}
'''
        return system_prompt

    def get_next_action(self, goal: str, current_page: BrowserState, 
                        session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]) -> BrowserAction:
        system_prompt = self.get_system_prompt(goal)
        current_state_msg = self.format_state_into_chat(current_page, goal)
        history = self.format_actions_into_chats(session_history)

        # Append current_state_msg to history
        history.append(current_state_msg)

        # Increase temperature on failures
        if session_history:
            last_action_result = session_history[-1]
            if last_action_result.result.outcome == BrowserActionOutcome['SUCCESS']:
                self.temperature = 0
            else:
                self.temperature = min(1.0, self.temperature + 0.3)

        response = self.generate_content(system_prompt, history, tools, self.temperature)

        print(response)

        function_call = response['candidates'][0]['content']['parts'][0]['functionCall']
        token_count = response['usageMetadata']['totalTokenCount']

        print (f"Token Usage: {token_count}")

        args = {k: v for k, v in function_call['args'].items() if k != 'reasoning'}
        return BrowserAction(function_call['name'], args, function_call['args']['reasoning'])



