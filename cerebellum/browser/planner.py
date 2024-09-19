import html
import json
import random
import string
from bs4 import BeautifulSoup
import requests
import json
from playwright.sync_api import Page
from typing import List, Dict, Any
from cerebellum.core import AbstractPlanner, SupervisorPlanner, RecordedAction
from cerebellum.browser.types import BrowserAction, BrowserActionOutcome, BrowserActionResult, BrowserState

tools = [
            {
                "name": "click",
                "description": "Initiate a mouse click on the intended HTML element",
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
                "name": "check",
                "description": "Check a checkbox or radio button",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": '''A CSS selector targeting the element to click, the target element MUST match a css selector from 'Checkable Elements'. use the following priority order for CSS selectors:
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
                "name": "select",
                "description": 'Select the values for a <select> tag',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": '''A CSS selector targeting the select element, the target element MUST match a css selector from 'Selectable Elements'. use the following priority order for CSS selectors:
  1. ID-based selectors (e.g., 'tag#id') - ALWAYS prefer these if available
  2. Unique class-based selectors
  3. Attribute selectors
  4. Combination of tag and class/attribute''',
                        },
                        "values": {
                            "type": "array",
                            "description": "The value(s) that should be selected. For non multiple select, there should only be one value",
                            "items": {
                                "type": "string"
                            }
                        },
                    },
                    "required": ["reasoning", "css_selector", "values"],
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
                "name": "goto",
                "description": "Navigate the page to a new URL. This is the same as setting 'window.location.href'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "href": {
                            "type": "string",
                            "description": "The URL you want the page to navigate to. This is the same as setting 'window.location.href'",
                        },
                    },
                    "required": ["reasoning", "href"],
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

class GeminiBrowserPlanner(AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult]):
    tool_config = {
        "function_calling_config": {
            "mode": "ANY",
            "allowed_function_names": ["click", "fill", "check", "select", "focus", "goto", "achieved", "unreachable"]
        },
    }

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash-exp-0827", vertex_location: str = None, vertex_project_id: str = None):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = 0

        if vertex_location and vertex_project_id:
            self.use_vertex = True
            self.location = vertex_location
            self.project_id = vertex_project_id
        else:
            self.use_vertex = False
        

    def get_vertex_config(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' 
        }

        url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_name}:generateContent"

        print(url)

        return (headers, url)


    def get_ai_studio_config(self):
        headers = {
            'Content-Type': 'application/json',
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        return (headers, url)

    @classmethod
    def format_tools_to_openapi(cls, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        openapi_schema = {
            "type": "OBJECT",
            "properties": {
                "1_prior_steps": {
                    "type": "STRING",
                    "description": "Your concise summary of prior steps and their outcomes"
                },
                "2_current_state": {
                    "type": "STRING",
                    "description": "Your concise summary of the current webpage. Always describe the current state of any visible forms"
                },
                "3_top_5_potential_actions": {
                    "type": "ARRAY",
                    "description": "Plan out the 5 best actions to move closer to your goal",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "action": {"type": "STRING"},
                        }
                    }
                },
                "4_action_analysis": {
                    "type": "STRING",
                    "description": "Analyze the potential actions and assess the best one"
                },
                "5_next_action": {
                    "type": "STRING",
                    "description": "The name of the next action or recognition that the goal has been achieved or is impossible",
                    "enum": [tool["name"] for tool in tools]
                },
                "6_css_selector": {
                    "type": "STRING",
                    "description": "A CSS selector targeting the element which the next action is meant for"
                },
                "7_values": {
                    "type": "ARRAY",
                    "description": "Values to set on the targeted element for the next action",
                    "items": {
                        "type": "STRING",
                    }
                }
            },
            "required": ["1_prior_steps", "2_current_state", "3_top_5_potential_actions", "4_action_analysis", "5_next_action", "6_css_selector", "7_values"]
        }

        # for tool in tools:
        #     action_schema = {
        #         "type": "object",
        #         "properties": {
        #             "name": {"type": "string", "enum": [tool["name"]]},
        #             "parameters": tool["parameters"]
        #         },
        #         "required": ["name", "parameters"]
        #     }
        #     openapi_schema["properties"]["next_browser_action"]["oneOf"].append(action_schema)

        print(json.dumps(openapi_schema, indent=2))

        return openapi_schema

    def generate_content(self, system_instructions: str, contents: List[Dict[str, Any]], tools: List[Dict[str, Any]], temperature=0) -> Dict[str, Any]:
        if (self.use_vertex):
            headers, url = self.get_vertex_config()
        else:
            headers, url = self.get_ai_studio_config()
      
        
        payload = {
            "system_instruction": {
                "parts": {
                    "text": system_instructions
                }
            },
            "contents": contents,
            "generation_config": {
                "temperature": temperature,
                "response_mime_type": "application/json",
                "response_schema": GeminiBrowserPlanner.format_tools_to_openapi(tools)
            }
        }
        
        print('Calling Gemini')
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        print(response)

        return response.json()


    def format_actions_into_chats(self, session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]):
        chat_messages = []
        for past_action in session_history:
            parts = []

            if past_action.state.screenshot_viewport:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": past_action.state.screenshot_viewport
                    }
                })
                parts.append({"text": "Viewport screenshot"})

            parts.append([
                {"text": f"URL: {past_action.state.url}"},
            ])
            
            chat_messages.append({
                "role": "user",
                "parts": parts
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
        checkable_selectors = '\n'.join(state.checkable_selectors)
        selectable_selectors = '\n'.join([selector for selector, options in state.selectable_selectors.items()])
        input_state_text = '\n'.join([f"{selector}: {value}" for selector, value in state.input_state.items()])
        chat_message["parts"].extend([
            {"text": f"URL: {state.url}"},
            {"text": f"HTML:\n{state.html}"},
            {"text": f"Clickable Elements\n###\n{clickable_selectors}\n###"},
            {"text": f"Fillable Elements\n###\n{fillable_selectors}\n###"},
            {"text": f"Checkable Elements\n###\n{checkable_selectors}\n###"},
            {"text": f"Selectable Elements\n###\n{selectable_selectors}\n###"},
            {"text": f"Input Element States: ###\n{input_state_text}\n###\n"}
        ])

        return chat_message
    
    def get_system_prompt(self, goal: str):
        system_prompt = f'''
You are a helpful assistant with tool calling capabilities. You have expert knowledge in CSS, HTML, playwright, puppeteer and CSS selectors.

Given a webpage's HTML and full + viewport screenshot, please respond with a JSON for a function call with its proper arguments that takes the next action toward completing the goal below. Follow all key considerations in crafting your function call.

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
* A radio button input is selected when it has the 'checked' attribute, (i.e. checked="checked")
* A checkbox input is selected when it has the 'checked' attribute, (i.e. checked="checked")
* Click to select or check radio buttons and checkboxes
* Target element argument of click() functionCall must match a css selector from 'Clickable Elements'
* Target element argument of fill() functionCall must match a css selector from 'Fillable Elements'
* If you believe the goal cannot be achieved, call the "unreachable" function. 
* If you believe the HTML and viewport screenshot shows that the goal has already been achieved without any further action from the user or you, call the "achieved" function.
* Always explain your reasoning the "reasoning" argument to the function called.
* Always press ENTER after filling the last or only input field.
* Solve captcha pages if they come up.
* If your goal appear unreachable, try searching.

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
                self.temperature = 1
            else:
                self.temperature = min(1.0, self.temperature + 0.3)

        response = self.generate_content(system_prompt, history, tools, self.temperature)

        print(response)

        function_call = json.loads(response['candidates'][0]['content']['parts'][0]['text'])

        # Create a BrowserAction from the function_call
        action_name = function_call['5_next_action']
        
        # Find the corresponding tool definition
        tool_def = next((tool for tool in tools if tool['name'] == action_name), None)
        
        if tool_def is None:
            raise ValueError(f"No tool definition found for action: {action_name}")
        
        # Prepare the args dictionary
        args = {}
        if 'css_selector' in tool_def['parameters']['properties']:
            args['css_selector'] = function_call['6_css_selector']
        
        if 'text' in tool_def['parameters']['properties']:
            args['text'] = function_call['7_values'][0] if function_call['7_values'] else ''
        
        if 'values' in tool_def['parameters']['properties']:
            args['values'] = function_call['7_values']
        
        if 'press_enter' in tool_def['parameters']['properties']:
            args['press_enter'] = False
        
        # Create the BrowserAction object
        browser_action = BrowserAction(
            function=action_name,
            args=args,
            prior_steps=function_call['1_prior_steps'],
            current_state=function_call['2_current_state'],
            top_5_actions=[action['action'] for action in function_call['3_top_5_potential_actions']],
            action_analysis=function_call['4_action_analysis']
        )

        return browser_action



class OpenAIBrowserPlanner(AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult]):

    def __init__(self, api_key: str, model_name: str = "gpt-4o", vision_capabale: bool = False, origin = "https://api.openai.com"):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = 0
        self.vision_capabale = vision_capabale
        self.origin = origin

    def generate_content(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], temperature=0) -> Dict[str, Any]:
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": tool
            })
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "tools": openai_tools,
            "tool_choice": "required",
            "temperature": temperature
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' 
        }
        
        url = f"{self.origin}/v1/chat/completions"
        
        print('Calling OpenAI')

        print(payload["messages"])
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        print(response)

        return response.json()


    def format_actions_into_chats(self, session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]):
        chat_messages = []
        for index, past_action in enumerate(session_history):
            # Add the state as a user message
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"URL at step {index}: {past_action.state.url}"
                    }
                ]
            }
            if self.vision_capabale and past_action.state.screenshot_viewport:
                user_message["content"].append({
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{past_action.state.screenshot_viewport}"
                        }
                    }
                })

            
            chat_messages.append(user_message)

            call_id = f'call_{"".join(random.choices(string.ascii_letters + string.digits, k=24))}'
            
            # Add the action as an assistant message
            arg_dict = past_action.action.args.copy()
            arg_dict['reasoning'] = past_action.action.reason
            assistant_message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": call_id,
                    "function": {
                            "name": past_action.action.function,
                            "arguments": json.dumps(arg_dict)
                    },
                    "type": "function"
                }]
            }
            chat_messages.append(assistant_message)
            
            # Add the result as a function message
            function_message = {
                "role": "tool",
                "content": json.dumps({
                    "name": past_action.action.function,
                    "outcome": past_action.result.outcome,
                    "url": past_action.result.url
                }),
                "tool_call_id": call_id
            }
            chat_messages.append(function_message)
        return chat_messages
    

    def format_state_into_chat(self, state: BrowserState, goal: str):
        clickable_selectors = '\n'.join(state.clickable_selectors)
        fillable_selectors = '\n'.join(state.fillable_selectors)
        checkable_selectors = '\n'.join(state.checkable_selectors)

        print(state.selectable_selectors)

        selectable_selectors = '\n'.join([f"{selector}: {', '.join(options)}" for selector, options in state.selectable_selectors.items()])

        text_state = []
        text_state.append(f"Current URL:\n{state.url}\n")
        text_state.append(f"Current HTML:\n{state.html}\n")
        text_state.append(f"Clickable Elements\n###\n{clickable_selectors}\n###")
        text_state.append(f"\nFillable Elements: ###\n{fillable_selectors}\n###\n")
        text_state.append(f"\nCheckable Elements: ###\n{checkable_selectors}\n###\n")
        text_state.append(f"\nSelectable Elements: ###\n{selectable_selectors}\n###\n")
        
        input_state_text = '\n'.join([f"{selector}: {value}" for selector, value in state.input_state.items()])
        text_state.append(f"\nInput Element States: ###\n{input_state_text}\n###\n")

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": ''.join(text_state)
                }
            ]
        }

        if self.vision_capabale and state.screenshot_viewport:
            user_message["content"].append({
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{state.screenshot_viewport}"
                    }
                }
            })

        if self.vision_capabale and state.screenshot_full:
                user_message["content"].append({
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{state.screenshot_full}"
                        }
                    }
                })

        return user_message
    
    def get_system_prompt(self, goal: str):
        system_prompt = f'''
You are a helpful assistant with tool calling capabilities. You have expert knowledge in CSS, HTML, playwright, puppeteer and CSS selectors.

Given a webpage's HTML and full + viewport screenshot, please respond with a JSON for a function call with its proper arguments that takes the next action toward completing the goal below. Follow all key considerations in crafting your function call.

Key considerations:
* Only consider the goal achieved if and only if the current state and function call history achieves ALL parts of the goal
* A goal is not achieved if you believe there is one or more additional action necessary (i.e clicking, filling, submitting)
* ALWAYS GENERATE 5 POTENTIAL ACTIONS
* Verify search results align with the goal; don't assume accuracy
* You are provided with a "viewport" view of the webpage and a full screenshot of the entire webpage.
* When selecting elements, use the following priority order for CSS selectors:
  1. ID-based selectors (e.g., 'tag#id') - ALWAYS prefer these if available
  2. Unique class-based selectors
  3. Attribute selectors
  4. Combination of tag and class/attribute
* A radio button input is selected when it has the 'checked' attribute, (i.e. checked="checked")
* A checkbox input is selected when it has the 'checked' attribute, (i.e. checked="checked")
* Use "check" function for checking radio buttons and checkboxes
* Use "select" function for setting values in select elements
* Always select ALL desired values for a select element in one function call
* Target element argument of click() functionCall must match a css selector from 'Clickable Elements'
* Target element argument of fill() functionCall must match a css selector from 'Fillable Elements'
* Target element argument of check() functionCall must match a css selector from 'Checkable Elements'
* Target element argument of select() functionCall must match a css selector from 'Selectable Elements'
* If you believe the goal cannot be achieved, call the "unreachable" function. 
* If you believe the HTML and viewport screenshot shows that the goal has already been achieved without any further action from the user or you, call the "achieved" function.
* Always explain your reasoning the "reasoning" argument to the function called.
* Always press ENTER after filling the last or only input field.
* Solve captcha pages if they come up.
* If your goal appear unreachable, try searching.

Goal: 
{goal}
'''
        return {
            "role": "system",
            "content": system_prompt
        }

    def get_next_action(self, goal: str, current_page: BrowserState, 
                        session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]) -> BrowserAction:
        system_prompt = self.get_system_prompt(goal)
        current_state_msg = self.format_state_into_chat(current_page, goal)
        history = self.format_actions_into_chats(session_history)

        # Append current_state_msg to history
        history.insert(0, system_prompt)
        history.append(current_state_msg)

        # Increase temperature on failures
        if session_history:
            last_action_result = session_history[-1]
            if last_action_result.result.outcome == BrowserActionOutcome['SUCCESS']:
                self.temperature = 1
            else:
                self.temperature = min(1.0, self.temperature + 0.3)

        response = self.generate_content(history, tools, self.temperature)

        print(response)

        function_call = response["choices"][0]["message"]['tool_calls'][0]["function"]
        raw_args = json.loads(function_call['arguments'])

        args = {k: v for k, v in raw_args.items() if k != 'reasoning'}
        return BrowserAction(function_call['name'], args, raw_args['reasoning'])

