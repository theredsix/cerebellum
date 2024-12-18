"""vLLM planner module for browser automation.

This module provides the vLLMPlanner class which uses vLLM's OpenAI compatible API
to control browser actions. It handles screenshot analysis, coordinate transformations,
and maintains browser state.

Typical usage example:

    planner = AnthropicPlanner(api_key="key123")
    action = planner.plan_action(goal="Click login button", 
                               current_state=browser_state)
"""

import base64
import copy
import io
import json
import random
import requests
from dataclasses import asdict, dataclass
from datetime import datetime
from math import floor
from typing import Any, cast, Optional, Union

from openai import Client
import openai.types.chat as chat
from cerebellum.browser import (
    ActionPlanner,
    BrowserAction,
    BrowserActionType,
    BrowserState,
    BrowserStep,
    Coordinate,
    ScrollBar,
)
from PIL import Image, ImageDraw
from cerebellum.planners.shared import CURSOR_BYTES, MsgOptions, ScalingRatio
from typing import Literal, Union
from pydantic import BaseModel, Field

class vLLMPotentialAction(BaseModel):
    potential_action_1: str
    potential_action_2: str
    potential_action_3: str
    potential_action_4: str
    potential_action_5: str

class vLLMAction(BaseModel):
    action: BrowserActionType
    coordinate: Coordinate
    text: str

class TypeStr(BaseModel):
    name: Literal["type"]
    text: str

class KeyStroke(BaseModel):
    name: Literal["key"] 
    text: str

class MouseMove(BaseModel):
    name: Literal["mouse_move"]
    coordinate: list[int]

class Wait(BaseModel):
    name: Literal["wait"]
    seconds: int

class LeftClick(BaseModel):
    name: Literal["left_click"]

class LeftClickDrag(BaseModel):
    name: Literal["left_click_drag"]
    coordinate: list[float]

class RightClick(BaseModel):
    name: Literal["right_click"]

class DoubleClick(BaseModel):
    name: Literal["double_click"]

class Screenshot(BaseModel):
    name: Literal["screenshot"]

class SwitchTab(BaseModel):
    name: Literal["switch_tab"]
    tab_id: int

class StopBrowsing(BaseModel):
    name: Literal["stop_browsing"] 
    success: bool
    error: Optional[str] = None


class vLLMResponse(BaseModel):
    review_of_prior_steps: str
    current_state: str
    current_mouse_analysis: str
    current_active_element: str
    potential_actions: vLLMPotentialAction
    potential_action_analysis: str
    next_action_plan: str
    next_action: Union[MouseMove, LeftClick, TypeStr, KeyStroke, LeftClickDrag, RightClick, DoubleClick, Screenshot, Wait, SwitchTab, StopBrowsing] = Field(discriminator="name")

tools = [
    {
        "type": "function",
        "function": {
            "name": "type",
            "description": "Type a string of text on the keyboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "description": "The string of text to type.",
                        "type": "string"
                    }
                },
                "required": ["text"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "key",
            "description": "Press a key or key-combination on the keyboard. This supports xdotool's `key` syntax. Examples: 'a', 'Return', 'alt+Tab', 'ctrl+s', 'Up', 'KP_0' (for the numpad 0 key).",
            "parameters": {
                "properties": {
                    "text": {
                        "description": "The key or key-combination to press.",
                        "type": "string"
                    }
                },
                "required": ["text"],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type",
            "description": "Type a string of text on the keyboard.",
            "parameters": {
                "properties": {
                    "text": {
                        "description": "The string of text to type.",
                        "type": "string"
                    }
                },
                "required": ["text"],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_move",
            "description": "Move the cursor to a specified (x, y) pixel coordinate on the screen.",
            "parameters": {
                "properties": {
                    "coordinate": {
                        "description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to.",
                        "type": "array"
                    }
                },
                "required": ["coordinate"],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "left_click",
            "description": "Click the left mouse button.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "left_click_drag",
            "description": "Click and drag the cursor to a specified (x, y) pixel coordinate on the screen.",
            "parameters": {
                "properties": {
                    "coordinate": {
                        "description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to drag the mouse to.",
                        "type": "array"
                    }
                },
                "required": ["coordinate"],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "right_click",
            "description": "Click the right mouse button.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "double_click",
            "description": "Double-click the left mouse button.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_tab",
            "description": "Call this function to switch the active browser tab to a new one",
            "input_schema": {
                "type": "object",
                "properties": {
                    "tab_id": {
                        "type": "integer",
                        "description": "The ID of the tab to switch to",
                    },
                },
                "required": ["tab_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_browsing",
            "description": "Call this function when you have achieved the goal of the task.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "Whether the task was successful",
                    },
                    "error": {
                        "type": "string",
                        "description": "The error message if the task was not successful",
                    },
                },
                "required": ["success"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Take a screenshot of the screen.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait a number of seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                     "seconds": {
                        "description": "The number of seconds to wait.",
                        "type": "integer"
                    }
                },
                "required": ["seconds"],
            }
        }
    }
]



@dataclass(frozen=True)
class vLLMPlannerOptions:
    """Configuration options for the Anthropic planner.

    Args:
        screenshot_history: Number of previous screenshots to include in context.
        mouse_jitter_reduction: Pixel threshold for mouse movement jitter reduction.
        api_key: Anthropic API key for authentication.
        client: Pre-configured Anthropic client instance.
        debug_image_path: Path to save debug images.
    """

    model: str
    server: str
    screenshot_history: Optional[int] = None
    mouse_jitter_reduction: Optional[int] = None
    api_key: Optional[str] = None
    debug_image_path: Optional[str] = None



class vLLMPlanner(ActionPlanner):
    """A planner that uses  vLLM's OpenAI compatible API to control browser actions.

    This planner interfaces with Claude to interpret browser state and determine
    appropriate actions to achieve user goals. It handles screenshot analysis,
    mouse movements, keyboard input, and maintains context of the browsing session.

    Attributes:
        screenshot_history: Number of previous screenshots to include in context
        mouse_jitter_reduction: Pixel threshold for reducing mouse movement jitter
        input_token_usage: Count of tokens used in API requests
        output_token_usage: Count of tokens used in API responses
        debug_image_path: Optional path to save debug screenshots
        model: The model name used for vLLM
        host: The host address for the vLLM API
        port: The port number for the vLLM API
        debug: Whether debug mode is enabled
    """

    def __init__(self, options: vLLMPlannerOptions) -> None:
        """Initializes the Anthropic planner.

        Args:
            options: Configuration options for the planner. If None, uses defaults.
        """
        super().__init__()

        self.server = options.server
        self.model = options.model
        
        self.screenshot_history: int = (
            options.screenshot_history
            if options and options.screenshot_history is not None
            else 1
        )
        self.mouse_jitter_reduction: int = (
            options.mouse_jitter_reduction
            if options and options.mouse_jitter_reduction is not None
            else 5
        )
        self.input_token_usage: int = 0
        self.output_token_usage: int = 0
        self.debug_image_path: Optional[str] = (
            options.debug_image_path if options else None
        )
        self.debug: bool = False

    def format_system_prompt(
        self, goal: str, additional_context: str, additional_instructions: list[str]
    ) -> str:
        """Formats the system prompt for the model.

        Constructs a system prompt that provides instructions and context to the model
        about how to interact with the browser environment.

        Args:
            goal: The user's goal/task to accomplish
            additional_context: Extra context information to help accomplish the goal
            additional_instructions: List of additional instructions to include

        Returns:
            A formatted system prompt string
        """
        instructions = "\n".join(
            f"* {instruction}" for instruction in additional_instructions
        )
        prompt = f"""
<SYSTEM_CAPABILITY>
* You are a computer use tool that is controlling a browser in fullscreen mode to complete a goal for the user. The goal is listed below in <USER_TASK>.
* The browser operates in fullscreen mode, meaning you must accomplish your task solely by interacting with the website's user interface or calling "switch_tab" or "stop_browsing"
* All mouse coordinates are normalized to integers between 0 and 1000, where 0 represents the minimum position and 1000 represents the maximum position on both axes
* After each action, you will be provided with mouse position, open tabs, and a screenshot of the active browser tab.
* When reviewing past actions, you will receive:
  - "prior_steps_summary": A summary of all actions taken so far in the session and their outcomes. This summary will NOT include the most recent attempted action which will be described separately for you to verify.
  - "most_recent_attempted_action": The last action plan that was executed, which you should verify was completed successfully
* Use the Page_down or Page_up keys to scroll through the webpage. If the website is scrollable, a gray rectangle-shaped scrollbar will appear on the right edge of the screenshot. Ensure you have scrolled through the entire page before concluding that content is unavailable.
* The mouse cursor will appear as a black arrow in the screenshot. Use its position to confirm whether your mouse movement actions have been executed successfully. Ensure the cursor is correctly positioned over the intended UI element before executing a click command.
* The active element (e.g. text input field, button, link) is outlined with a red bounding box. Use this visual indicator to confirm which element currently has focus and will receive keyboard input.
* Some actions may take time to process - if clicking an element doesn't produce immediate results, wait briefly and take another screenshot to verify the outcome.
* After each action, you will receive information about open browser tabs. This information will be in the form of a list of JSON objects, each representing a browser tab with the following fields:
  - "tab_id": An integer that identifies the tab within the browser. Use this ID to switch between tabs.
  - "title": A string representing the title of the webpage loaded in the tab.
  - "active_tab": A boolean indicating whether this tab is currently active. You will receive a screenshot of the active tab.
  - "new_tab": A boolean indicating whether the tab was opened as a result of the last action.
* Follow all directions from the <IMPORTANT> section below. 
* The current date is {datetime.now().isoformat()}.
</SYSTEM_CAPABILITY>

You have access to the following tools:
<FUNCTION_CALLS>
{json.dumps(tools, indent=2)}
</FUNCTION_CALLS>

<REASONING_PROCESS>
The user will ask you to perform a task and you should use their browser to do so.For each action you take, you must follow this exact reasoning process:

1. OBSERVATION:
   - Understand the past steps taken to achieve the goal
   - Verify if the last action was successful
   - Record the past steps summary along with success of the last action in the "review_of_prior_steps" field
   - Describe the current browser state, and screenshotas they relate to our goal in the "current_state" field
   - Analyze mouse position relative to UI elements in "current_mouse_analysis"
   - Analyze the active element (outlined in red rectangle) in "current_active_element" by describing:
     * Element type (button, input field, link, etc.)
     * Current value/state (text content, selected/unselected, enabled/disabled)
     * Visibility status (fully visible, partially obscured, scrolled out of view)
     * Size and position relative to viewport
     * Interactive state (clickable, focusable, read-only)

2. PLANNING:
   - Generate 5 potential actions given the current screenshot that will bring you closer to the goal. These actions must align with a <FUNCTION_CALLS>
   - Each potential action should be a concise, single-sentence description of an action that can be performed on the current screenshot. Only suggest actions that are immediately possible, not future steps.
   - Record the potential actions in the "potential_action_N" field where N is the number of the potential action

3. ANALYSIS:
   - For each potential action, carefully evaluate if the action is possible given the current screenshot and if it will bring you closer to the goal
   - Combine and record the analysis in the "potential_action_analysis" field

4. DECISION:
   - Select the single most appropriate potential action based on your analysis
   - Explain why this element is the best choice for progressing toward the goal
   - Describe exactly what you expect to change in the browser state after this action. Your description must be specific and measurable, not vague. For example:
     * Good: "The username input field will contain 'johndoe@email.com'"
     * Bad: "The login form will be filled out"
     * Good: "The website will navigate to 'checkout'"
     * Bad: "We'll proceed to checkout"
     * Good: "The page will scroll down revealing the footer section"
     * Bad: "We'll look for more content"
   - Record the selected action along with the desired outcome in "next_action_plan" field

5. ACTION:
   - Convert your chosen action from "next_action_plan" into a tool call JSON format using one of the available <FUNCTION_CALLS> and store it in "next_action"

You must structure your response following these exact steps before taking any action.
</REASONING_PROCESS>

<IMPORTANT>
* Move mouse to element's center before clicking.
* Always target the center of an element's bounding box for mouse movements
* Before issuing a 'type' action:
  - Verify the target input field is the active element (outlined with a red bounding box)
  - If not active, first move the mouse and click to focus the field
  - Only proceed with typing once the field is properly focused and active
* You will use information provided in user's <USER DATA> to fill out forms on the way to your goal.
* Ensure that any UI element is completely visible on the screen before attempting to interact with it.
* When clicking on elements, ensure the cursor tip is positioned in the center of the element, not on its edges.
* If an element fails to respond after clicking, try adjusting the cursor position so the tip falls directly on the center of the element and try again.
* {instructions}
</IMPORTANT>"""

        return prompt.strip()

    def create_tool_use_id(self) -> str:
        """Creates a unique tool use ID.

        Generates a random ID string with a specific prefix for tool use tracking.

        Returns:
            A unique tool use ID string
        """
        prefix = "toolu_01"
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        id_length = 22
        result = prefix

        for _ in range(id_length):
            result += random.choice(characters)

        return result

    def mark_screenshot(
        self, img_buffer: bytes, mouse_position: Coordinate, scrollbar: ScrollBar, active_element: Union[tuple[Coordinate, Coordinate], None]
    ) -> bytes:
        """Adds scrollbar and cursor overlays to a screenshot.

        Args:
            img_buffer: Raw bytes of the screenshot image
            mouse_position: Coordinate object containing x,y position of mouse cursor
            scrollbar: ScrollBar object containing scrollbar dimensions and position

        Returns:
            Raw bytes of the modified screenshot with overlays added

        Raises:
            IOError: If there are issues manipulating the image
        """
        with Image.open(io.BytesIO(img_buffer)) as img:
            width, height = img.size

            # Create scrollbar overlay
            scrollbar_width = 10
            scrollbar_height = int(height * scrollbar.height)
            scrollbar_top = int(height * scrollbar.offset)

            # Create gray rectangle for scrollbar
            # 0.7 opacity = 179 in 8-bit alpha (0.7 * 255 ≈ 179)
            scrollbar_img = Image.new(
                "RGBA", (scrollbar_width, scrollbar_height), (128, 128, 128, 179)
            )

            # Create composite image
            composite = img.copy()
            composite.paste(scrollbar_img, (width - scrollbar_width, scrollbar_top))

            # Add cursor
            cursor_img = Image.open(io.BytesIO(CURSOR_BYTES))
            composite.paste(
                cursor_img,
                (
                    max(0, mouse_position.x - cursor_img.width // 2),
                    max(0, mouse_position.y - cursor_img.height // 2),
                ),
                cursor_img,
            )

            # Draw bounding box around active element if it exists
            if active_element:
                draw = ImageDraw.Draw(composite)
                
                # Extract coordinates
                top_left = active_element[0]
                dimensions = active_element[1]

                # Calculate box coordinates
                x1 = top_left.x
                y1 = top_left.y
                x2 = x1 + dimensions.x
                y2 = y1 + dimensions.y

                # Ensure coordinates stay within image bounds
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))
                
                # Draw red rectangle with width 2
                draw.rectangle([(x1, y1), (x2, y2)], outline='red', width=2, fill=None)

            # Convert back to bytes
            output_buffer = io.BytesIO()
            composite.save(output_buffer, format="PNG")
            return output_buffer.getvalue()

    def resize_screenshot(self, screenshot_buffer: bytes) -> bytes:
        """Resizes a screenshot to standard dimensions while maintaining aspect ratio.

        Args:
            screenshot_buffer: Raw bytes of the screenshot image

        Returns:
            Raw bytes of the resized screenshot

        Raises:
            IOError: If there are issues manipulating the image
        """
        with Image.open(io.BytesIO(screenshot_buffer)) as img:
            target_width = 1280
            target_height = 800

            # Calculate dimensions that fit within target while maintaining aspect ratio
            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

            output_buffer = io.BytesIO()
            img.save(output_buffer, format="PNG")
            return output_buffer.getvalue()

    def resize_image_to_dimensions(
        self, screenshot_buffer: bytes, new_dim: Coordinate
    ) -> bytes:
        """Resizes an image to specified dimensions. Ignores aspect ratio.

        Args:
            screenshot_buffer: Raw bytes of the screenshot image
            new_dim: Coordinate object containing target width and height

        Returns:
            Raw bytes of the resized image

        Raises:
            IOError: If there are issues manipulating the image
        """
        with Image.open(io.BytesIO(screenshot_buffer)) as img:
            resized = img.resize((new_dim.x, new_dim.y), Image.Resampling.LANCZOS)
            output_buffer = io.BytesIO()
            resized.save(output_buffer, format="PNG")
            return output_buffer.getvalue()

    def get_scaling_ratio(self, orig_size: Coordinate) -> ScalingRatio:
        """Calculates scaling ratios to standardize image dimensions.

        This function calculates the scaling ratio to standardize the image dimensions to
        1000x1000 without maintaining the aspect ratio.
        Args:
            orig_size: Coordinate object containing original width and height

        Returns:
            ScalingRatio object containing scale factors and dimensions
        """
        # Calculate scaling ratios to standardize to 1000x1000
        width_ratio = orig_size.x / 1000
        height_ratio = orig_size.y / 1000
        
        return ScalingRatio(
            ratio_x=width_ratio,
            ratio_y=height_ratio,
            old_size=orig_size,
            new_size=Coordinate(x=1000, y=1000),
        )

    def browser_to_llm_coordinates(
        self, input_coords: Coordinate, scaling: ScalingRatio
    ) -> Coordinate:
        """Converts browser coordinates to LLM-scaled coordinates.

        Args:
            input_coords: Coordinate object containing browser x,y coordinates
            scaling: ScalingRatio object containing scale factors

        Returns:
            Coordinate object containing scaled coordinates
        """
        return Coordinate(
            x=min(max(floor(input_coords.x / scaling.ratio_x), 1), scaling.new_size.x),
            y=min(max(floor(input_coords.y / scaling.ratio_y), 1), scaling.new_size.y),
        )

    def llm_to_browser_coordinates(
        self, input_coords: Coordinate, scaling: ScalingRatio
    ) -> Coordinate:
        """Converts LLM-scaled coordinates back to browser coordinates.

        Args:
            input_coords: Coordinate object containing LLM x,y coordinates
            scaling: ScalingRatio object containing scale factors

        Returns:
            Coordinate object containing browser coordinates
        """
        return Coordinate(
            x=min(max(floor(input_coords.x * scaling.ratio_x), 1), scaling.old_size.x),
            y=min(max(floor(input_coords.y * scaling.ratio_y), 1), scaling.old_size.y),
        )

    def format_state_into_msg(
        self, tool_call_id: str, current_state: BrowserState, options: MsgOptions
    ) -> dict:
        """Formats browser state into a message for the LLM.

        Takes the current browser state and formats it into a message that can be sent to
        the LLM, including mouse position, URL, and screenshot if specified in options.

        Args:
            tool_call_id: Unique identifier for the tool call
            current_state: Current state of the browser including coordinates and screenshot
            options: Configuration options for what to include in the message

        Returns:
            A formatted message object compatible with Anthropic's API
        """
        result_text = ""
        content_sub_msg: list[any] = []

        if options.mouse_position:
            img_dim = Coordinate(x=current_state.width, y=current_state.height)
            scaling = self.get_scaling_ratio(img_dim)
            scaled_coord = self.browser_to_llm_coordinates(current_state.mouse, scaling)
            result_text += f"Mouse location: {json.dumps(asdict(scaled_coord))}\n\n"

        if options.tabs:
            tabs_as_dicts = [
                {
                    "tab_id": tab.id,
                    "title": tab.title,
                    "active_tab": tab.active,
                    "new_tab": tab.new,
                }
                for tab in current_state.tabs
            ]

            result_text += f"\n\nOpen Browser Tabs: {json.dumps(tabs_as_dicts)}\n\n"

        if options.screenshot:
            # result_text += "Here is a screenshot of the browser after the action was performed.\n\n"
            img_buffer = base64.b64decode(current_state.screenshot)
            viewport_image = self.resize_image_to_dimensions(
                img_buffer, Coordinate(x=current_state.width, y=current_state.height)
            )
            marked_image = self.mark_screenshot(
                viewport_image, current_state.mouse, current_state.scrollbar, current_state.active_element
            )
            resized = self.resize_screenshot(marked_image)

            if self.debug_image_path:
                with open(self.debug_image_path, "wb") as f:
                    f.write(resized)

            content_sub_msg.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(resized).decode()}",
                    },
                }
            )

        if result_text:  # Put a generic text explanation for no URL or result
            content_sub_msg.insert(0, {"type": "text", "text": result_text.strip()})


        return {
            "role": "tool",
            "content": content_sub_msg,
            "tool_call_id": tool_call_id,
        }

    def format_into_messages(
        self,
        goal: str,
        additional_context: str,
        current_state: BrowserState,
        session_history: list[BrowserStep],
    ) -> list[dict]:
        """Formats a complete conversation history into messages for the LLM.

        Takes the goal, context and browser history and formats them into a sequence of
        messages that can be sent to the LLM to provide full context of the interaction.

        Args:
            goal: The task goal to be accomplished
            additional_context: Extra context information for the task
            current_state: Current state of the browser
            session_history: List of previous browser steps and actions

        Returns:
            A list of formatted message objects for the Anthropic API

        Raises:
            None
        """
        messages: list[Any] = []
        tool_id = self.create_tool_use_id()

        user_prompt = f"""Please complete the following task:
<USER_TASK>
{goal}
</USER_TASK>

Using the supporting contextual data:
<USER_DATA>
{additional_context}
</USER_DATA>"""

        msg0 = {
            "role": "user",
            "content": [{"type": "text", "text": user_prompt.strip()}],
        }

        if session_history:
            last_step = session_history[-1]

            # Update tool ID for next action
            tool_id = last_step.action.id or self.create_tool_use_id()

            inflated_reasoning = json.loads(last_step.action.reasoning)

            state = {
                "prior_steps_summary": inflated_reasoning["review_of_prior_steps"],
                "most_recent_attempted_action": inflated_reasoning["next_action_plan"],
            }

            msg1 = {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(state),
                    }
                ],
                "tool_calls": [
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {
                            "name": last_step.action.action,
                            "arguments": self.flatten_browser_step_to_action(last_step),
                        },
                    }
                ],
            }
        else:
            state = {
                "prior_steps_summary": "No past actions have been taken.",
                "most_recent_attempted_action": "Grab a screenshot of the browser to understand what is the starting website state.",
            }

            msg1 = {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(state),
                    }
                ],
                "tool_calls": [
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {
                            "name": "screenshot", 
                            "arguments": "{}",
                        }
                    }
                ],
            }
        
        messages.append(msg0)
        messages.append(msg1)

        current_state_message = self.format_state_into_msg(
            tool_id,
            current_state,
            MsgOptions(mouse_position=True, screenshot=True, tabs=True),
        )
        messages.append(current_state_message)

        return messages

    def parse_action(
        self, message: vLLMResponse, scaling: ScalingRatio, current_state: BrowserState
    ) -> BrowserAction:
        """Parses an LLM message into a browser action.

        Takes a message from the LLM and converts it into a concrete browser action,
        handling coordinate conversions and special cases.

        Args:
            message: The message from the LLM containing the action
            scaling: Scaling ratios for coordinate conversion
            current_state: Current state of the browser

        Returns:
            A BrowserAction object representing the parsed action

        Raises:
            None
        """
        # Collect all text content as reasoning
        raw_message = message.model_dump()
        del raw_message["next_action"]
        reasoning = json.dumps(raw_message)
        id = self.create_tool_use_id()
        last_message = message.next_action

        if last_message.name == "stop_browsing":
            if not last_message.success:
                return BrowserAction(
                    action=BrowserActionType.FAILURE,
                    reasoning=reasoning,
                    text= last_message.error if last_message.error else "Unknown Error",
                    coordinate=None,
                    id=id,
                )
            return BrowserAction(
                action=BrowserActionType.SUCCESS,
                reasoning=reasoning,
                text=None,
                coordinate=None,
                id=id,
            )

        if last_message.name == "switch_tab":
            if "tab_id" not in last_message:
                return BrowserAction(
                    action=BrowserActionType.FAILURE,
                    reasoning=reasoning,
                    text="No tab id for switch_tab function call",
                    coordinate=None,
                    id=id,
                )
            return BrowserAction(
                action=BrowserActionType.SWITCH_TAB,
                reasoning=reasoning,
                text=str(
                    last_message.tab_id
                ),  # Convert to string since text is Optional[str]
                coordinate=None,
                id=last_message.id,
            )

        if last_message.name == "key" or last_message.name == "type":
            if last_message.name == "key":
                # Handle special key mappings from utils.parse_xdotool
                text_lower = last_message.text.lower().strip()
                if text_lower in ("page_down", "pagedown"):
                    return BrowserAction(
                        action=BrowserActionType.SCROLL_DOWN,
                        reasoning=reasoning,
                        coordinate=None,
                        text=None,
                        id=id,
                    )
                if text_lower in ("page_up", "pageup"):
                    return BrowserAction(
                        action=BrowserActionType.SCROLL_UP,
                        reasoning=reasoning,
                        coordinate=None,
                        text=None,
                        id=id,
                    )

            return BrowserAction(
                action=(
                    BrowserActionType.KEY if last_message.name == "key" else BrowserActionType.TYPE
                ),
                reasoning=reasoning,
                text=last_message.text,
                coordinate=None,
                id=id,
            )

        elif last_message.name == "mouse_move":
            browser_coordinates = self.llm_to_browser_coordinates(
                Coordinate(x=last_message.coordinate[0], y=last_message.coordinate[1]), scaling
            )

            # Calculate the distance moved
            distance_moved = (
                (browser_coordinates.x - current_state.mouse.x) ** 2
                + (browser_coordinates.y - current_state.mouse.y) ** 2
            ) ** 0.5
            print(f"Distance moved: {distance_moved}")

            # Check if the movement is within a minimal threshold to consider as jitter
            if distance_moved <= self.mouse_jitter_reduction:
                print("Minimal mouse movement detected, considering as jitter.")
                return BrowserAction(
                    action=BrowserActionType.LEFT_CLICK,
                    reasoning=reasoning,
                    coordinate=None,
                    text=None,
                    id=id,
                )

            return BrowserAction(
                action=BrowserActionType.MOUSE_MOVE,
                reasoning=reasoning,
                coordinate=browser_coordinates,
                text=None,
                id=id,
            )

        elif last_message.name == "left_click_drag":
            browser_coordinates = self.llm_to_browser_coordinates(
                Coordinate(x=last_message.coordinate[0], y=last_message.coordinate[1]), scaling
            )

            return BrowserAction(
                action=BrowserActionType.LEFT_CLICK_DRAG,
                reasoning=reasoning,
                coordinate=browser_coordinates,
                text=None,
                id=id,
            )

        elif last_message.name in (
            "left_click",
            "right_click",
            "middle_click",
            "double_click",
            "screenshot",
            "cursor_position",
        ):
            action_type = {
                "left_click": BrowserActionType.LEFT_CLICK,
                "right_click": BrowserActionType.RIGHT_CLICK,
                "middle_click": BrowserActionType.MIDDLE_CLICK,
                "double_click": BrowserActionType.DOUBLE_CLICK,
                "screenshot": BrowserActionType.SCREENSHOT,
                "cursor_position": BrowserActionType.CURSOR_POSITION,
            }[last_message.name]

            return BrowserAction(
                action=action_type,
                reasoning=reasoning,
                coordinate=None,
                text=None,
                id=id,
            )

        else:
            return BrowserAction(
                action=BrowserActionType.FAILURE,
                reasoning=reasoning,
                text=f"Unsupported computer action: {last_message.name}",
                coordinate=None,
                id=id,
            )

    def plan_action(
        self,
        goal: str,
        additional_context: str,
        additional_instructions: list[str],
        current_state: BrowserState,
        session_history: list[BrowserStep],
    ) -> BrowserAction:
        system_prompt = self.format_system_prompt(
            goal, additional_context, additional_instructions
        )

        system_msg = {
            "role": "system",
            "content": system_prompt
        }

        messages = self.format_into_messages(
            goal, additional_context, current_state, session_history
        )

        messages.insert(0, system_msg)

        scaling = self.get_scaling_ratio(
            Coordinate(x=current_state.width, y=current_state.height)
        )

        json_schema = vLLMResponse.model_json_schema()

        body = {
            "model": self.model,
            "messages": messages,
            "guided_json": json_schema,
            "temperature": 0.2
        }

        headers = {
            "Content-Type": "application/json"
        }

        print("\nMessages sent to API:")
        print(self.print_messages(messages))

        raw = requests.post(
            url=f"{self.server}/v1/chat/completions",
            headers=headers,
            data=json.dumps(body),
        )

        if raw.status_code != 200:
            print(raw.text)
            raise Exception(f"Failed to get response from API: {raw.status_code}")

        raw_json = raw.json()
        
        content = raw_json["choices"][0]["message"]["content"]

        response = vLLMResponse.model_validate_json(content)

        print(json.dumps(response.model_dump(), indent=4))

        self.input_token_usage  += raw_json["usage"]["prompt_tokens"]
        self.output_token_usage += raw_json["usage"]["completion_tokens"]

        print(
            f"Cumulative token usage - Input: {self.input_token_usage}, Output: {self.output_token_usage}, Total: {self.input_token_usage + self.output_token_usage}"
        )

        action = self.parse_action(response, scaling, current_state)
        print(action)

        return action

    def flatten_browser_step_to_action(self, step: BrowserStep) -> str:
        if step.action.action == BrowserActionType.SCROLL_DOWN:
            return {"text": "Page_Down"}

        elif step.action.action == BrowserActionType.SCROLL_UP:
            return {"text": "Page_Up"}

        val: dict[str, Any] = {}

        if step.action.text:
            val["text"] = step.action.text

        if step.action.coordinate:
            img_dim = Coordinate(x=step.state.width, y=step.state.height)
            scaling = self.get_scaling_ratio(img_dim)
            llm_coordinates = self.browser_to_llm_coordinates(
                step.action.coordinate, scaling
            )
            val["coordinate"] = [llm_coordinates.x, llm_coordinates.y]

        return json.dumps(val)
    
    def print_messages(self, messages: list[dict[str, any]]):
        """Pretty prints messages after removing image data.
        
        Args:
            messages: List of message dictionaries to print
        """
        for msg in messages:
            # Create a copy to modify
            msg_copy = copy.deepcopy(msg)
            
            # Remove image URLs from content if present
            if "content" in msg_copy and isinstance(msg_copy["content"], list):
                msg_copy["content"] = [
                    item for item in msg_copy["content"] 
                    if isinstance(item, dict) and item.get("type") != "image_url"
                ]
            
            print(json.dumps(msg_copy, indent=4))
            print()
