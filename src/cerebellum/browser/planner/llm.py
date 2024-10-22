import copy
import json
from typing import Dict, Any, Tuple
from cerebellum.core import AbstractPlanner
from cerebellum.browser.types import BrowserAction, BrowserActionResult, BrowserState

class AbstractLLMBrowserPlanner(AbstractPlanner[BrowserState, BrowserAction, BrowserActionResult]):

    tools = [
            {
                "name": "click",
                "description": "Initiate a mouse click on the intended HTML element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "css_selector_index": {
                            "type": "number",
                            "description": 'The numeric index of the css_selector from "Clickable Elements". A click action will be performed on the element targeted by the css selector.',
                        }
                    },
                    "required": ["css_selector_index"],
                },
            },
            {
                "name": "check",
                "description": "Check a checkbox or radio button",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "css_selector_index": {
                            "type": "number",
                            "description": 'The numeric index of the css_selector from "Checkable Elements". A check toggle action will be performed on the element targeted by the css selector.',
                        }
                    },
                    "required": ["css_selector_index"],
                },
            },
            {
                "name": "fill",
                "description": 'Fill in the <input>, <textarea>, or [contenteditable] element with the specified text. Do not target input[type="hidden"] elements',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "css_selector_index": {
                            "type": "number",
                            "description": 'The numeric index of the css_selector from "Fillable Elements". A fill action will be performed on the element targeted by the css selector.',
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
                    "required": ["css_selector_index", "text", "press_enter"],
                },
            },
            {
                "name": "select",
                "description": 'Select the values for a <select> tag',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "css_selector_index": {
                            "type": "number",
                            "description": 'The numeric index of the css_selector from "Selectable Elements". A select action will be performed on the element targeted by the css selector.',
                        },
                        "values": {
                            "type": "array",
                            "description": "The value(s) that should be selected. For non multiple select, there should only be one value",
                            "items": {
                                "type": "string"
                            }
                        },
                    },
                    "required": ["css_selector_index", "values"],
                },
            },
            {
                "name": "goto",
                "description": "Navigate the page to a new URL. This is the same as setting 'window.location.href'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "href": {
                            "type": "string",
                            "description": "The URL you want the page to navigate to. This is the same as setting 'window.location.href'",
                        },
                    },
                    "required": ["href"],
                },
            },
            {
                "name": "wait",
                "description": "Wait for loading or processing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "wait_in_seconds": {
                            "type": "number",
                            "description": "The number of seconds to wait, use 5 as a default if you are unsure",
                        },
                    },
                    "required": ["wait_in_seconds"],
                },
            },
            {
                "name": "achieved",
                "description": "Call this function when the goal has been achieved.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                },
            },
            {
                "name": "unreachable",
                "description": "Call this function when if you believe the goal cannot be achieved.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                },
            },
        ]

    @classmethod
    def get_system_role(cls):
        return 'You are a helpful assistant with tool calling capabilities. You have expert knowledge in CSS, HTML, playwright, puppeteer and CSS selectors.'

    @classmethod
    def get_system_functions_declaration(cls):
        return f'''
You have access to the following function calls:

{json.dumps(AbstractLLMBrowserPlanner.tools, indent=2)}
'''

    @classmethod
    def get_system_instructions(cls):
        return f'''
Given a webpage's HTML and full + viewport screenshot, please respond with a JSON for a function call with its proper arguments that takes the next action toward completing the goal below. Follow all key considerations in crafting your function call.
'''
    @classmethod
    def get_system_key_considerations(cls):
        return f'''
Key considerations:
* Only consider the goal achieved if and only if the current state and function call history achieves ALL parts of the goal
* A goal is not achieved if you believe there is one or more additional action necessary (i.e clicking, filling, submitting)
* Only use data from "additional_context" when filling out forms. DO NOT MAKE UP OR HALLUCINATE ANSWERS
* Verify search results align with the goal; don't assume accuracy
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
* If you believe current state shows that the goal has already been achieved without any further action from the user or you, call the "achieved" function.
* Always press ENTER after filling the last or only input field.
* Solve captcha pages if they come up.
* If your goal appear unreachable, try searching.
'''
    
    @classmethod
    def get_system_additional_context(cls, additional_context: Dict[str, Any] | None):
        return f'''Additional Context: ###
{json.dumps(additional_context, indent=2) if additional_context else "None"}
###'''
    
    @classmethod
    def stringify_selector_and_inputs(cls, state: BrowserState):
        clickable_selectors = '\n'.join([f"{index}: {selector}" for index, selector in enumerate(state.clickable_selectors)])
        fillable_selectors = '\n'.join([f"{index}: {selector}" for index, selector in enumerate(state.fillable_selectors)])
        checkable_selectors = '\n'.join([f"{index}: {selector}" for index, selector in enumerate(state.checkable_selectors)])
        selectable_selectors = '\n'.join([f"{index}: {selector}\t{', '.join(options)}" for index, (selector, options) in enumerate(state.selectable_selectors.items())])

        text_state = {}
        text_state["url"] = f"Current URL:\n{state.url}\n"
        text_state["html"] = f"Current HTML:\n{state.html}\n"
        text_state["clickable"] = f"Clickable Elements\n###\n{clickable_selectors}\n###"
        text_state["fillable"] = f"\nFillable Elements: ###\n{fillable_selectors}\n###\n"
        text_state["checkable"] = f"\nCheckable Elements: ###\n{checkable_selectors}\n###\n"
        text_state["selectable"] = f"\nSelectable Elements: ###\n{selectable_selectors}\n###\n"
        
        input_state_text = '\n'.join([f"{selector}: {value}" for selector, value in state.input_state.items()])
        text_state["input"] = f"\nInput Element States: ###\n{input_state_text}\n###\n"

        print(text_state["clickable"])
        print(text_state["fillable"])
        print(text_state["checkable"])
        print(text_state["selectable"])

        return text_state


    @classmethod
    def convert_tools_to_structured_json(cls, state: BrowserState, disable_additional_properties: bool = False):
        openapi_tools = []
        for tool in copy.deepcopy(cls.tools):
            openapi_tool = tool["parameters"]
            
            openapi_tool["properties"] = {
                tool["name"]: {
                    "type": "string",
                    "description": tool["description"],
                    "enum": [tool["name"]]
                },
                "name": {
                    "type": "string",
                    "description": "The name of the action to take",
                    "enum": [tool["name"]]
                },
                **openapi_tool["properties"]
            }

            # css_enum = None
            # if tool["name"] == "click":
            #     if not state.clickable_selectors:
            #         continue
            #     css_enum = state.clickable_selectors
            # elif tool["name"] == "check":
            #     if not state.checkable_selectors:
            #         continue
            #     css_enum = state.checkable_selectors
            # elif tool["name"] == "select":
            #     if not state.selectable_selectors:
            #         continue
            #     css_enum = list(state.selectable_selectors.keys())                
            # elif tool["name"] == "fill":
            #     if not state.fillable_selectors:
            #         continue
            #     css_enum = state.fillable_selectors

            # if css_enum:
            #     css_enum = [x.replace("\\", "\\\\\\\\") for x in css_enum]
            #     css_enum = [x.replace('"', "\\'") for x in css_enum]
            #     openapi_tool["properties"]["css_selector_index"]["enum"] = css_enum
            
            openapi_tool["required"].insert(0, "name")
            openapi_tool["required"].insert(0, tool["name"])

            if disable_additional_properties:
                openapi_tool["additionalProperties"] = False

            openapi_tools.append(openapi_tool)
        return openapi_tools
    
    @classmethod
    def parse_function_call(cls, response: Dict[str, Any], state: BrowserState,) -> Tuple[str, Dict[str, Any]]:
        action_name = response["name"]
        args = {}

        if "text" in response:
            args["text"] = response["text"]
        
        if "css_selector_index" in response:
            css_selector_list = []
            if action_name == "click":
                css_selector_list = state.clickable_selectors
            if action_name == "check":
                css_selector_list = state.checkable_selectors
            elif action_name == "select":
                css_selector_list = [x for x in state.selectable_selectors.keys()]
            elif action_name == "fill":
                css_selector_list = state.fillable_selectors

            if css_selector_list:
                css_selector_index = response["css_selector_index"]
                args["css_selector"] = css_selector_list[css_selector_index]
        
        if "press_enter" in response:
            args["press_enter"] = response["press_enter"]
        
        if "values" in response:
            args["values"] = response["values"]
        
        if "href" in response:
            args["href"] = response["href"]

        if "wait_in_seconds" in response:
            args["wait_in_seconds"] = response["wait_in_seconds"]

        return (action_name, args)