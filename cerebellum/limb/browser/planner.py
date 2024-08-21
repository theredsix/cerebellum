import json
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
                        "target_element": {
                            "type": "object",
                            "description": "The target element to click",
                            "properties": {
                                "tag": {
                                    "type": "string",
                                    "description": "The HTML tag name of the target element (e.g., 'button', 'a', 'div')"
                                },
                                "css_classes": {
                                    "type": "array",
                                    "description": "CSS classes of the target element. Always include all css classnames of the target element.",
                                    "items": {
                                        "type": "string",
                                    }
                                },
                                "element_id": {
                                    "type": "string",
                                    "description": "The id attribute of the target element. Do not include this property if the element does not have an id.",
                                }
                            },
                            "required": ["tag"],        
                        }
                    },
                    "required": ["reasoning", "target_element"],
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
                        "target_element": {
                            "type": "object",
                            "description": "The target element to click",
                            "properties": {
                                "tag": {
                                    "type": "string",
                                    "description": "The HTML tag name of the target element (e.g., 'button', 'a', 'div')"
                                },
                                "css_classes": {
                                    "type": "array",
                                    "description": "CSS classes of the target element. Always include all css classnames of the target element.",
                                    "items": {
                                        "type": "string",
                                    }
                                },
                                "element_id": {
                                    "type": "string",
                                    "description": "The id attribute of the target element. Do not include this property if the element does not have an id.",
                                }
                            },
                            "required": ["tag"],        
                        },
                        "text": {
                            "type": "string",
                            "description": "The text that should be filled into the input element.",
                        },
                        "press_enter": {
                            "type": "boolean",
                            "description": "If true, the input will be filled and the enter key will be pressed. This is helpful for form or search submissions",
                        },
                    },
                    "required": ["reasoning", "target_element", "text", "press_enter"],
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
                        "target_element": {
                            "type": "object",
                            "description": "The target element to click",
                            "properties": {
                                "tag": {
                                    "type": "string",
                                    "description": "The HTML tag name of the target element (e.g., 'button', 'a', 'div')"
                                },
                                "css_classes": {
                                    "type": "array",
                                    "description": "CSS classes of the target element. Always include all css classnames of the target element.",
                                    "items": {
                                        "type": "string",
                                    }
                                },
                                "element_id": {
                                    "type": "string",
                                    "description": "The id attribute of the target element. Do not include this property if the element does not have an id.",
                                }
                            },
                            "required": ["tag"],        
                        },
                    },
                    "required": ["reasoning", "target_element"],
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
                button {{ background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }}
            </style>
        </head>
        <body>
            <h1>Action Review</h1>
            <div id="recommended-action">
                <h2>Recommended Action</h2>
                <p id="rec-function"></p>
                <p id="rec-reasoning"></p>
                <p id="rec-css-selector"></p>
                <p id="rec-text"></p>
            </div>
            <div id="custom-action">
                <h2>Custom Action</h2>
                <label for="function">Function:</label>
                <select id="function">
                    <option value="click">Click</option>
                    <option value="fill">Fill</option>
                    <option value="focus">Focus</option>
                    <option value="achieved">Achieved</option>
                    <option value="unreachable">Unreachable</option>
                </select>
                <label for="reasoning">Reasoning:</label>
                <input type="text" id="reasoning">
                <label for="css-selector">CSS Selector:</label>
                <input type="text" id="css-selector">
                <label for="text">Text (for fill action):</label>
                <input type="text" id="text">
                <label for="press-enter">Press Enter (for fill action):</label>
                <input type="checkbox" id="press-enter">
                <button onclick="submitCustomAction()">Submit Custom Action</button>
            </div>
            <script>
                function updateRecommendedAction(action) {{
                    $('#rec-function').text('Function: ' + action.function);
                    $('#rec-reasoning').text('Reasoning: ' + action.args.reasoning);
                    $('#rec-css-selector').text('CSS Selector: ' + (action.args.css_selector || 'N/A'));
                    $('#rec-text').text('Text: ' + (action.args.text || 'N/A'));
                }}
                function submitCustomAction() {{
                    var action = {{
                        function: $('#function').val(),
                        args: {{
                            reasoning: $('#reasoning').val(),
                            css_selector: $('#css-selector').val(),
                            text: $('#text').val(),
                            press_enter: $('#press-enter').is(':checked')
                        }}
                    }};
                    // Send action back to Python
                    window.pywebview.api.submit_custom_action(JSON.stringify(action));
                }}
            </script>
        </body>
        </html>
        """

        # Update the display page with the HTML content
        self.display_page.set_content(html_content)

        # Display the recommended action
        self.display_page.evaluate(f"updateRecommendedAction({json.dumps(recommended_action)})")

        # Wait for user input
        custom_action = None
        while custom_action is None:
            custom_action = self.display_page.evaluate("window.customAction")

        # Parse the custom action
        parsed_action = json.loads(custom_action)
        return BrowserAction(
            function=parsed_action['function'],
            args=parsed_action['args']
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
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))

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
    

    def format_state_into_chat(self, state: BrowserState):
        chat_message = {
            "role": "user",
            "parts": [
                { "inline_data": 
                    {
                        "mime_type":"image/jpeg",
                        "data": state.screenshot_full
                    }
                },
                {"text": f"Full webpage screenshot"},
            ]
        }

        if state.screenshot_viewport != state.screenshot_full:
            chat_message["parts"].extend([
                { "inline_data": 
                    {
                        "mime_type":"image/jpeg",
                        "data": state.screenshot_viewport
                    }
                },
                {"text": f"Viewport screenshot"},
            ])

        chat_message["parts"].extend([
            {"text": f"URL: {state.url}"},
            {"text": f"HTML:\n{state.html}"},
        ])

        return chat_message
    
    def get_system_prompt(self, goal: str):
        system_prompt = f'''
You are an expert developer in CSS and HTML with an excellent knowledge of jQuery and CSS selectors.
Given a webpage's HTML and full + viewport screenshot, decide the best action to take to complete the following goal.

Key considerations:
* Only consider the goal achieved if and only if the current state and function call history achieves ALL parts of the goal
* A goal is not achieved if you believe there is one or more additional action necessary (i.e clicking, filling, submitting)
* Exclude <input type="hidden"> elements from target elements
* Verify search results align with the goal; don't assume accuracy
* You are provided with a "viewport" view of the webpage and a full screenshot of the entire webpage.
* Always include the target element's id attribute if it exists.
* Always include all css classnames of the target element.
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
        current_state_msg = self.format_state_into_chat(current_page)
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



