from guidance import models, gen, system, user, assistant, role, select
from guidance.chat import Llama3ChatTemplate
import json
from core import AbstractPlanner, RecordedAction
import json
import random
import string
import json
from playwright.sync_api import Page
from typing import List, Dict, Any
from browser.planner.llm import AbstractLLMBrowserPlanner
from core import AbstractPlanner, RecordedAction
from cerebellum.browser.types import BrowserAction, BrowserActionOutcome, BrowserActionResult, BrowserState

def tool_response(text=None, **kwargs):
    return role("tool_response", text, **kwargs)

class ExtendedLlama3ChatTemplate(Llama3ChatTemplate):
    def get_role_start(self, role_name):
        if role_name == "tool_response":
            return "<|start_header_id|>ipython<|end_header_id|>\n\n"
        else:
            return super().get_role_start(role_name)


class LocalLLMBrowserPlanner(AbstractLLMBrowserPlanner):

    def __init__(self, vision_capabale: bool = False):
        self.temperature = 0
        self.vision_capabale = vision_capabale
        self.llm = models.LlamaCpp("/usr/share/ollama/.ollama/models/blobs/sha256-09cd6813dc2e73d9db9345123ee1b3385bb7cee88a46f13dc37bc3d5e96ba3a4", 
                      echo=False,                      
                      chat_template=ExtendedLlama3ChatTemplate, n_ctx=12072, n_gpu_layers=35, verbose=True)

    def generate_content(self, state: BrowserState, messages: List[Dict[str, Any]], temperature=0) -> Dict[str, Any]:
        prompt = self.llm
        for message in messages:
            if message["role"] == "system":
                with system():
                    prompt = prompt + message["content"]
            elif message["role"] == "user":
                with user():
                    for content in message["content"]:
                        if content["type"] == "text":
                            prompt = prompt + content["text"]
            elif message["role"] == "assistant":
                with assistant():
                    prompt = prompt + f'{{"reasoning": "{message["function"]["reasoning"]}", "name": "{message["function"]["name"]}", "parameters": "{message["function"]["parameters"]}"}}'
            elif message["role"] == "tool":
                with tool_response():
                    response_part = message["content"]
                    prompt = prompt + f'{{"name": "{response_part["name"]}", "outcome": "{response_part["outcome"]}", "url": "{response_part["url"]}"}}'

        # After processing all messages, generate the response
        with assistant():
            response = prompt + '{ "prior_steps": "' + gen('prior_steps', stop_regex=',\s*"current_state"') + \
                ',\n"current_state": "' + gen('current_state', stop_regex=',\s*"potential_actions"') + \
                f''',\n"potential_actions": "Top 5 potential actions to advance towards goal in ANY ORDER are:
    *: {gen(stop='*:')}
    *: {gen(stop='*:')}
    *: {gen(stop='*:')}
    *: {gen(stop='*:')}
    *: {gen(stop='"action_analysis":')}''' + \
                '"action_analysis": "' + gen('action_analysis', stop_regex=',\s*"name"') + \
                f''',\n"name": "{select(["click","select", "check", "fill", "focus", "goto", "achieved", "unreachable"], name="name")}"'''
            
            print(response)

            function_name = response['name']
            reasoning = response['action_analysis']
            args = {}
            
            if response['name'] == 'click':
                response = response + f''', "parameters": {{"css_selector": "{select(state.clickable_selectors, name="css_selector")}"}}'''
                args['css_selector'] = response['css_selector']
            if response['name'] == 'check':
                response = response + f''', "parameters": {{"css_selector": "{select(state.checkable_selectors, name="css_selector")}"}}'''
                args['css_selector'] = response['css_selector']
            if response['name'] == 'select':
                response = response + f''', "parameters": {{"css_selector": "{select([key for key in state.selectable_selectors.keys()], name="css_selector")}", "values": ["{gen('values', stop=']')}]}}'''
                args['css_selector'] = response['css_selector']
                print(response['values'])
                args['values'] = json.loads('["' + response['values']+ ']')
            elif response['name'] == 'fill':
                response = response + f''', "parameters": {{"css_selector": "{select(state.fillable_selectors, name="css_selector")}", "text": ''' + \
                    gen('text', stop_regex=',\s*"press_enter"') + \
                    f''', "press_enter": {select(['true', 'false'], name='press_enter')}}}'''
                args['css_selector'] = response['css_selector']
                args['text'] = response['text'].strip('" ')
                args['press_enter'] = response['press_enter'].strip('" \n')
            elif response['name'] == 'focus':
                response = response + f''', "parameters": {{
                    "css_selector": {gen('css_selector', stop="}", regex="[^']")}
                }}'''
                args['css_selector'] = response['css_selector'].strip('" \n')
            elif response['name'] == 'goto':
                response = response + f''', "parameters": {{
                    "href": {gen('href', stop="}")}
                }}'''
                args['href'] = response['href'].strip('" \n')

            print('============================================\n', response, '\n============================================')

            return {
                "name": function_name, 
                "reasoning": reasoning, 
                "arguments": args
                }

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
            assistant_message = {
                "role": "assistant",
                "function": {
                        "reasoning": past_action.action.reason,
                        "name": past_action.action.function,
                        "parameters": json.dumps(past_action.action.args),
                },
            }
            chat_messages.append(assistant_message)
            
            # Add the result as a function message
            function_message = {
                "role": "tool",
                "content": {
                    "name": past_action.action.function,
                    "outcome": past_action.result.outcome,
                    "url": past_action.result.url
                },
                "tool_call_id": call_id
            }
            chat_messages.append(function_message)
        return chat_messages
    

    def format_state_into_chat(self, state: BrowserState, current_step: int):
        clickable_selectors = '\n'.join(state.clickable_selectors)
        fillable_selectors = '\n'.join(state.fillable_selectors)
        checkable_selectors = '\n'.join(state.checkable_selectors)
        selectable_selectors = '\n'.join([selector for selector, options in state.selectable_selectors.items()])

        text_state = []
        text_state.append(f"\nURL at step {current_step}:\n{state.url}\n")
        text_state.append(f"\nCurrent HTML:\n{state.html}\n")
        text_state.append(f"\nClickable Elements: ###\n{clickable_selectors}\n###\n")
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
        wrapped_tools = []
        for tool in LocalLLMBrowserPlanner.tools:
            tool_deep_copy = json.loads(json.dumps(tool))
            del tool_deep_copy["parameters"]["properties"]["reasoning"]
            if "required" in tool_deep_copy["parameters"]:
                tool_deep_copy["parameters"]["required"] = [param for param in tool_deep_copy["parameters"]["required"] if param != "reasoning"]
            wrapped_tools.append(json.dumps({
                "type": "function",
                "function": tool_deep_copy
            }, indent=2))

        wrapped_tools_str = '\n'.join(wrapped_tools)

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

Respond in the format {{"prior_steps": Your concise summary of prior steps and their outcomes, "current_state": Your concise summary of the current webpage. Always restate the current state of forms, "potential_actions": Plan out the 5 best actions to move closer to your goal, "action_analysis": Analyze the potential actions and assess the best one, "name": function name, "parameters": dictionary of argument name and its value}}. Do not use variables.

{wrapped_tools_str}

Goal: 
###
{goal}
###
'''
        return {
            "role": "system",
            "content": system_prompt
        }

    def get_next_action(self, goal: str, state: BrowserState, 
                        session_history: list[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]) -> BrowserAction:
        system_prompt = self.get_system_prompt(goal)
        current_state_msg = self.format_state_into_chat(state, len(session_history))
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

        response = self.generate_content(state, history, self.temperature)

        print(response)

        function_call = response["name"]
        args = response['arguments']

        return BrowserAction(function_call, args, response['reasoning'])



