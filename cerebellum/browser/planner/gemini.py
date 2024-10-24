import copy
import json
import random
import string
from typing import Any, Dict, List
from core import RecordedAction

import requests
from cerebellum.browser.types import BrowserAction, BrowserActionOutcome, BrowserActionResult, BrowserState
from cerebellum.browser.planner.llm import AbstractLLMBrowserPlanner

class GeminiBrowserPlanner(AbstractLLMBrowserPlanner):

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
    def format_tools_to_openapi(cls, current_page: BrowserState) -> Dict[str, Any]:
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
                    "type": "OBJECT",
                    "description": "Plan out the 5 best actions to move closer to your goal",
                    "properties": {
                        "potential_action_1": { "type": "STRING" },
                        "potential_action_2": { "type": "STRING" },
                        "potential_action_3": { "type": "STRING" },
                        "potential_action_4": { "type": "STRING" },
                        "potential_action_5": { "type": "STRING" },
                    }
                },
                "4_action_analysis": {
                    "type": "STRING",
                    "description": "Analyze the potential actions and assess the best one"
                },
                "5_next_action": {
                    "type": "STRING",
                    "description": "The name of the next action or recognition that the goal has been achieved or is impossible",
                    "enum": [tool["name"] for tool in GeminiBrowserPlanner.tools]
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
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
            ],
        }
        
        print('Calling Gemini')
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        print(response)

        return response.json()


    @classmethod
    def format_actions_into_chats(cls, session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]):
        chat_messages = []
        for past_action in session_history:
            parts = []

            if past_action.state.screenshot_full:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": past_action.state.screenshot_full
                    }
                })
                parts.append({"text": "Full page screenshot"})

            parts.append([
                {"text": f"URL: {past_action.state.url}"},
            ])
            
            chat_messages.append({
                "role": "user",
                "parts": parts
            })
            
            # Add the action as a model message
            arg_dict = past_action.action.args
            arg_dict['reasoning'] = past_action.action.action_analysis
            function_call_msg = {
                "role": "model",
                "parts": [
                    {
                        "text": json.dumps({
                            "functionCall": {
                                "name": past_action.action.function,
                                "args": arg_dict
                            }
                        })
                    }
                ]
            }
            chat_messages.append(function_call_msg)
            
            # Add the result as a function message
            function_response_msg = {
                "role": "user",
                "parts": [{
                    "text": json.dumps({
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
                    })
                }]
            }
            chat_messages.append(function_response_msg)
        
        return chat_messages
    
    @classmethod
    def format_state_into_chat(cls, state: BrowserState, goal: str):
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

        # if state.screenshot_viewport and state.screenshot_viewport != state.screenshot_full:
        #     chat_message["parts"].extend([
        #         { "inline_data": 
        #             {
        #                 "mime_type":"image/jpeg",
        #                 "data": state.screenshot_viewport
        #             }
        #         },
        #         {"text": f"Viewport screenshot"},
        #     ])

        string_state = cls.stringify_selector_and_inputs(state)
        chat_message["parts"].extend([
            {"text": string_state["url"]},
            {"text": string_state["html"]},
            {"text": string_state["clickable"]},
            {"text": string_state["fillable"]},
            {"text": string_state["checkable"]},
            {"text": string_state["selectable"]},
            {"text": string_state["input"]}
        ])

        return chat_message
    
    @classmethod
    def get_system_prompt(cls, goal: str):
        system_prompt = f'''{cls.system_role}

{cls.system_functions_declaration}

{cls.system_instructions}

{cls.system_key_considerations}

Goal: 
{goal}
'''
        return system_prompt

    def get_next_action(self, goal: str, current_page: BrowserState, 
                        session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]) -> BrowserAction:
        system_prompt = GeminiBrowserPlanner.get_system_prompt(goal)
        current_state_msg = GeminiBrowserPlanner.format_state_into_chat(current_page, goal)
        history = GeminiBrowserPlanner.format_actions_into_chats(session_history)

        # Append current_state_msg to history
        history.append(current_state_msg)

        # Increase temperature on failures
        if session_history:
            last_action_result = session_history[-1]
            if last_action_result.result.outcome == BrowserActionOutcome['SUCCESS']:
                self.temperature = 1
            else:
                self.temperature = min(1.0, self.temperature + 0.3)

        response = self.generate_content(system_prompt, history, current_page, self.temperature)

        print(response)

        function_call = json.loads(response['candidates'][0]['content']['parts'][0]['text'].replace("\\'", '\\"'))


        # Create a BrowserAction from the function_call
        action_name = function_call['5_next_action']
        
        # Find the corresponding tool definition
        tool_def = next((tool for tool in GeminiBrowserPlanner.tools if tool['name'] == action_name), None)
        
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
            args['press_enter'] = True

        if 'wait_in_seconds' in tool_def['parameters']['properties']:
            args['wait_in_seconds'] = 5

        # Create the BrowserAction object
        browser_action = BrowserAction(
            function=action_name,
            args=args,
            prior_steps=function_call['1_prior_steps'],
            current_state=function_call['2_current_state'],
            top_5_actions=[action for action in function_call['3_top_5_potential_actions'].values()],
            action_analysis=function_call['4_action_analysis']
        )

        return browser_action

