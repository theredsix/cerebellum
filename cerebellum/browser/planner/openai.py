import copy
import json
import random
import string
from typing import Any, Dict, List
from core import RecordedAction, TrainablePlanner

import requests
from cerebellum.browser.types import BrowserAction, BrowserActionOutcome, BrowserActionResult, BrowserState
from cerebellum.browser.planner.llm import AbstractLLMBrowserPlanner

class OpenAIBrowserPlanner(AbstractLLMBrowserPlanner, TrainablePlanner[List[Any], BrowserState, BrowserAction, BrowserActionResult]):

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", vision_capabale: bool = True, origin = "https://api.openai.com"):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = 0
        self.vision_capabale = vision_capabale
        self.origin = origin

    def generate_content(self, messages: List[Dict[str, Any]], schema: Dict[str, Any], temperature=0) -> Dict[str, Any]:
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": schema
            },
            "temperature": temperature
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' 
        }
        
        url = f"{self.origin}/v1/chat/completions"
        
        print('Calling OpenAI')
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print("Response body:", response.text)

        json_response = response.json()
        print(f"Tokens used: {json_response['usage']['total_tokens']}")

        return json_response

    @classmethod
    def format_actions_into_chats(cls, session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]], vision_capabale: bool, format_for_fine_tuning: bool = False):
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
            if vision_capabale and past_action.state.screenshot_full:
                user_message["content"].append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{past_action.state.screenshot_full}"
                        }
                    }
                )

            
            chat_messages.append(user_message)

            call_id = f'call_{"".join(random.choices(string.ascii_letters + string.digits, k=24))}'
            
            # Add the action as an assistant message
            arg_dict = past_action.action.args.copy()
            arg_dict['reasoning'] = past_action.action.action_analysis
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

            if format_for_fine_tuning:
                assistant_message["weight"] = 0

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
    
    @classmethod
    def format_state_into_chat(cls, state: BrowserState, vision_capabale: bool):
        string_state = cls.stringify_selector_and_inputs(state)

        text_state = []
        text_state.append(string_state["url"])
        text_state.append(string_state["html"])
        text_state.append(string_state["clickable"])
        text_state.append(string_state["fillable"])
        text_state.append(string_state["checkable"])
        text_state.append(string_state["selectable"])
        text_state.append(string_state["input"])
        
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": ''.join(text_state)
                }
            ]
        }

        # if vision_capabale and state.screenshot_viewport:
        #     user_message["content"].append(
        #         {
        #             "type": "image_url",
        #             "image_url": {
        #                 "url": f"data:image/jpeg;base64,{state.screenshot_viewport}"
        #             }
        #         }
        #     )

        if vision_capabale and state.screenshot_full:
                user_message["content"].append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{state.screenshot_full}"
                        }
                    }
                )

        return user_message
    
    @classmethod
    def get_system_prompt(cls, goal: str, additional_context: Dict[str, Any] | None):
        system_prompt = f'''{cls.get_system_role()}

{cls.get_system_functions_declaration()}

{cls.get_system_instructions()}

{cls.get_system_key_considerations()}

{cls.get_system_additional_context(additional_context)}

Goal: 
{goal}
'''
        return {
            "role": "system",
            "content": system_prompt
        }
    
    @classmethod
    def get_message_history(cls, goal: str, additional_context: Dict[str, Any] | None, current_page: BrowserState, 
                            session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]], vision_capabale: bool) -> List[Dict[str, Any]]:
        system_prompt = cls.get_system_prompt(goal, additional_context)
        current_state_msg = cls.format_state_into_chat(current_page, vision_capabale)
        history = cls.format_actions_into_chats(session_history, vision_capabale, True)

        # Append current_state_msg to history
        history.insert(0, system_prompt)
        history.append(current_state_msg)

        return history

    def get_next_action(self, goal: str, additional_context: Dict[str, Any] | None, current_page: BrowserState, 
                        session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]) -> BrowserAction:
        
        history = OpenAIBrowserPlanner.get_message_history(goal, additional_context, current_page, session_history, self.vision_capabale)

        # Increase temperature on failures
        if session_history:
            last_action_result = session_history[-1]
            if last_action_result.result.outcome == BrowserActionOutcome['SUCCESS']:
                self.temperature = 1
            else:
                self.temperature = min(1.0, self.temperature + 0.3)
        
        json_schema = {
            "name": "next_action_reasoning",
            "schema": {
                "type": "object",
                "properties": {
                    "prior_steps": {
                        "type": "string",
                        "description": "Your concise summary of prior steps and their outcomes"
                    },
                    "current_state": {
                        "type": "string",
                        "description": "Your concise summary of the current webpage. Always describe the current state of any visible forms"
                    },
                    "top_5_potential_actions": {
                        "type": "object",
                        "description": "Plan out the 5 best actions to move closer to your goal",
                        "properties": {
                            "potential_action_1": { "type": "string" },
                            "potential_action_2": { "type": "string" },
                            "potential_action_3": { "type": "string" },
                            "potential_action_4": { "type": "string" },
                            "potential_action_5": { "type": "string" },
                        },
                        "required": ["potential_action_1", "potential_action_2", "potential_action_3", "potential_action_4", "potential_action_5"],
                        "additionalProperties": False
                    },
                    "action_analysis": {
                        "type": "string",
                        "description": "Analyze the potential actions and assess the best one"
                    },
                    "next_action": {
                        "anyOf": AbstractLLMBrowserPlanner.convert_tools_to_structured_json(current_page, True)
                    }
                },
                "required": ["prior_steps", "current_state", "top_5_potential_actions", "action_analysis", "next_action"],
                "additionalProperties": False
            },
            "strict": True,
        }

        print(json.dumps(json_schema, indent=2))

        response = self.generate_content(history, json_schema, self.temperature)

        json_response = json.loads(response["choices"][0]["message"]['content'].replace("\\'", '\\"'))

        print(json.dumps(json_response, indent=2))

        (action_name, args) = AbstractLLMBrowserPlanner.parse_function_call(json_response["next_action"], current_page)
        
        browser_action = BrowserAction(
            function=action_name,
            args=args,
            prior_steps=json_response["prior_steps"],
            current_state=json_response["current_state"],
            top_5_actions=[
                json_response["top_5_potential_actions"]["potential_action_1"],
                json_response["top_5_potential_actions"]["potential_action_2"],
                json_response["top_5_potential_actions"]["potential_action_3"],
                json_response["top_5_potential_actions"]["potential_action_4"],
                json_response["top_5_potential_actions"]["potential_action_5"]
            ],
            action_analysis=json_response["action_analysis"]
        )
        
        return browser_action
    
    @classmethod
    def convert_into_training_examples(cls, goal: str, actions: List[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]], enable_vision: bool = True) -> List[Any]:
        training_examples = []

        for index in range(len(actions)):
            print(f"Processing action {index + 1}/{len(actions)}")
            session_history = actions[:index]
            action = actions[index].action
            state = actions[index].state
            messages = OpenAIBrowserPlanner.get_message_history(goal, state, session_history, enable_vision)

            inner_response = {
                    "prior_steps": action.prior_steps,
                    "current_state": action.current_state,
                    "top_5_potential_actions": {
                        "potential_action_1": action.top_5_actions[0],
                        "potential_action_2": action.top_5_actions[1],
                        "potential_action_3": action.top_5_actions[2],
                        "potential_action_4": action.top_5_actions[3],
                        "potential_action_5": action.top_5_actions[4],
                    },
                    "action_analysis": action.action_analysis,
                    "next_action": {
                        action.function: action.function,
                        "name": action.function,
                        **action.args
                    }
                }
            
            response = {
                "role": "assistant",
                "content": json.dumps(inner_response)
            }

            messages.append(response)

            training_examples.append({"messages": messages})

        return training_examples

