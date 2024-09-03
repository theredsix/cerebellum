from guidance import models, gen, system, user, assistant, role, select
from guidance.chat import Llama3ChatTemplate
import json
from core_abstractions import AbstractPlanner, RecordedAction
import json
import random
import string
import json
from playwright.sync_api import Page
from typing import List, Dict, Any
from cerebellum.limb.browser.planner import tools
from cerebellum.core_abstractions import AbstractPlanner, RecordedAction
from cerebellum.limb.browser.types import BrowserAction, BrowserActionOutcome, BrowserActionResult, BrowserState

def tool_response(text=None, **kwargs):
    return role("ipython", text, **kwargs)

class ExtendedLlama3ChatTemplate(Llama3ChatTemplate):
    def get_role_start(self, role_name):
        if role_name == "tool":
            return "<|start_header_id|>ipython<|end_header_id|>\n\n"
        else:
            return super().get_role_start(role_name)


class LocalLLMBrowserPlanner(AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult]):

    def __init__(self, vision_capabale: bool = False):
        self.temperature = 0
        self.vision_capabale = vision_capabale
        self.llm = models.LlamaCpp("/usr/share/ollama/.ollama/models/blobs/sha256-09cd6813dc2e73d9db9345123ee1b3385bb7cee88a46f13dc37bc3d5e96ba3a4", 
                      echo=False,                      
                      chat_template=ExtendedLlama3ChatTemplate, n_ctx=12072, n_gpu_layers=35, verbose=True)

    def generate_content(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], temperature=0) -> Dict[str, Any]:
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
                    prompt = role(message["role"], message["content"])

        # After processing all messages, generate the response
        with assistant():
            response = prompt + '{ "reasoning": "' + gen('reasoning', stop_regex=',\s*"name"') + \
                f'''", "name": "{select(["click", "fill", "focus", "goto", "achieved", "unreachable"], name="name")}"'''
            
            function_name = response['name']
            reasoning = response['reasoning']
            args = {}
            
            if response['name'] == 'click':
                response = response + f''', "parameters": {{
                    "css_selector": {gen('css_selector', stop="}")}
                }}'''
                args['css_selector'] = response['css_selector'].strip('" \n')
            elif response['name'] == 'fill':
                response = response + f''', "parameters": {{
                    "css_selector": {gen('css_selector', stop=',')}, "text": ''' + \
                    gen('text', stop_regex=',\s*"press_enter"') + \
                    f''', "press_enter": {select(['true', 'false'], name='press_enter')}
                }}'''
                args['css_selector'] = response['css_selector'].strip('" \n')
                args['text'] = response['text'].strip('" ')
                args['press_enter'] = response['press_enter'].strip('" \n')
            elif response['name'] == 'focus':
                response = response + f''', "parameters": {{
                    "css_selector": {gen('css_selector', stop="}")}
                }}'''
                args['css_selector'] = response['css_selector'].strip('" \n')
            elif response['name'] == 'goto':
                response = response + f''', "parameters": {{
                    "href": {gen('href', stop="}")}
                }}'''
                args['href'] = response['href'].strip('" \n')


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

        text_state = []
        text_state.append(f"Current URL:\n{state.url}\n")
        text_state.append(f"Current HTML:\n{state.html}\n")
        text_state.append(f"Clickable Elements\n###\n{clickable_selectors}\n###")
        text_state.append(f"Fillable Elements\n###\n{fillable_selectors}\n###")

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
        for tool in tools:
            tool_deep_copy = json.loads(json.dumps(tool))
            del tool_deep_copy["parameters"]["properties"]["reasoning"]
            if "required" in tool_deep_copy["parameters"]:
                tool_deep_copy["parameters"]["required"] = [param for param in tool_deep_copy["parameters"]["required"] if param != "reasoning"]
            print(tool_deep_copy)
            wrapped_tools.append(json.dumps({
                "type": "function",
                "function": tool
            }, indent=2))

        wrapped_tools_str = '\n'.join(wrapped_tools)

        system_prompt = f'''
You are a helpful assistant with tool calling capabilities. You have expert knowledge in CSS, HTML, playwright, puppeteer and CSS selectors.

Given a webpage's HTML and full + viewport screenshot, please respond with a JSON for a function call with its proper arguments that takes best action toward completing the goal below. Follow all key considerations in crafting your function call.

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
* If your goal appear unreachable, try searching.

Respond in the format {{"reasoning": Your concise step by step thoughts on the best next action,"name": function name, "parameters": dictionary of argument name and its value}}. Do not use variables.

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

        function_call = response["name"]
        args = response['arguments']

        return BrowserAction(function_call, args, response['reasoning'])



