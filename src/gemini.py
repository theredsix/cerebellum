import json
from session import PageAction, PageState, RecordedAction, Reasoner
from openapi import tools
import requests
import json
from typing import List, Dict, Any


tool_config = {
  "function_calling_config": {
    "mode": "ANY",
    "allowed_function_names": ["click", "fill", "focus", "achieved", "unreachable"]
  },
}

class GoogleGeminiReasoner(Reasoner):
    api_key: str

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro-latest"):
        self.api_key = api_key
        self.model_name = model_name


    def generate_content(self, system_instructions: str, contents: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            "tool_config": tool_config
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        return response.json()


    def format_actions_into_chats(self, session_history: list[RecordedAction]):
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
                                "outcome": past_action.result.outcome.value,
                                "url": past_action.result.url
                            }
                        }
                    }
                }]
            }
            chat_messages.append(function_response_msg)
        
        return chat_messages
    

    def format_state_into_chat(self, state: PageState):
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
* You are provided with a "viewport" view of the webpage and a full screenshot of the entire webpage.
* Only use html tag, class and id attributes in CSS selectors.
* Cannot use descendant, child or sibling CSS selectors.
* If you believe the goal cannot be achieved, call the "unreachable" function. 
* If you believe the HTML and viewport screenshot shows that the goal has already been achieved, call the "achieved" function.
* Always explain your reasoning the "reasoning" argument to the function called.
* Always press ENTER after filling the last or only input field.
* Solve captcha pages if they come up.
* If you are unsure of which input to fill or button to click, choose a child of the most correlated element

Goal: 
{goal}
'''
        return system_prompt


    def get_next_action(self, goal: str, current_page: PageState, session_history: list[RecordedAction]) -> PageAction:
        system_prompt = self.get_system_prompt(goal)
        current_state_msg = self.format_state_into_chat(current_page)
        history = self.format_actions_into_chats(session_history)

        # Append current_state_msg to history
        history.append(current_state_msg)

        response = self.generate_content(system_prompt, history, tools)

        function_call = response['candidates'][0]['content']['parts'][0]['functionCall']
        token_count = response['usageMetadata']['totalTokenCount']

        print (f"Token Usage: {token_count}")

        args = {k: v for k, v in function_call['args'].items() if k != 'reasoning'}
        return PageAction(function_call['name'], args, function_call['args']['reasoning'])



