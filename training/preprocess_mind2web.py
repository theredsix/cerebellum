"""
Example usage:
--------------
python mind2web_script.py --dataset_name osunlp/Multimodal-Mind2Web --subset train --output_dir mind2web
--------------

This script converts the Jupyter Notebook logic into a single Python script. 
It processes a dataset of browser steps (via the `datasets` library) and 
generates JSONL output for each task, representing the "cerebellum steps."
"""

import argparse
import base64
import dataclasses
import json
import math
import random
from dataclasses import dataclass, asdict
from io import BytesIO
from typing import List, Literal, Tuple, Union

from datasets import load_dataset
from PIL import Image, ImageDraw

from pydantic import BaseModel
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import os

# Base64 encoded cursor image
CURSOR_64 = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAQCAYAAAAvf+5AAAAAw3pUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjabVBRDsMgCP33FDuC8ijF49i1S3aDHX9YcLFLX+ITeOSJpOPzfqVHBxVOvKwqVSQbuHKlZoFmRzu5ZD55rvX8Uk9Dz2Ql2A1PVaJ/1MvPwK9m0TIZ6TOE7SpUDn/9M4qH0CciC/YwqmEEcqGEQYsvSNV1/sJ25CvUTxqBjzGJU86rbW9f7B0QHSjIxoD6AOiHE1oXjAlqjQVyxmTMkJjEFnK3p4H0BSRiWUv/cuYLAAABhWlDQ1BJQ0MgcHJvZmlsZQAAeJx9kT1Iw0AYht+2SqVUHCwo0iFD1cWCqIijVqEIFUKt0KqDyaV/0KQhSXFxFFwLDv4sVh1cnHV1cBUEwR8QZwcnRRcp8buk0CLGg7t7eO97X+6+A/yNClPNrnFA1SwjnUwI2dyqEHxFCFEM0DoqMVOfE8UUPMfXPXx8v4vzLO+6P0evkjcZ4BOIZ5luWMQbxNObls55nzjCSpJCfE48ZtAFiR+5Lrv8xrnosJ9nRoxMep44QiwUO1juYFYyVOIp4piiapTvz7qscN7irFZqrHVP/sJwXltZ5jrNKJJYxBJECJBRQxkVWIjTrpFiIk3nCQ//kOMXySWTqwxGjgVUoUJy/OB/8Lu3ZmFywk0KJ4DuF9v+GAaCu0Czbtvfx7bdPAECz8CV1vZXG8DMJ+n1thY7Avq2gYvrtibvAZc7wOCTLhmSIwVo+gsF4P2MvikH9N8CoTW3b61znD4AGepV6gY4OARGipS97vHuns6+/VvT6t8Ph1lyr0hzlCAAAA14aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOjFiYzFkZjE3LWM5YmMtNGYzZi1hMmEzLTlmODkyNWNiZjY4OSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo4YTUyMWJhMC00YmNlLTQzZWEtYjgyYS04ZGM2MTBjYmZlOTgiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplODQ3ZjUxNC00MWVlLTQ2ZjYtOTllNC1kNjI3MjMxMjhlZTIiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE3MzAxNTc3NjY5MTI3ODciCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zOCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQ6MTA6MjhUMTY6MjI6NDYtMDc6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDI0OjEwOjI4VDE2OjIyOjQ2LTA3OjAwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZTVjOTM2ZDYtYjMzYi00NzM4LTlhNWUtYjM3YTA5MzdjZDAxIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyNC0xMC0yOFQxNjoyMjo0Ni0wNzowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz5/5aQ8AAAABmJLR0QAcgByAAAtJLTuAAAACXBIWXMAAABZAAAAWQGqnamGAAAAB3RJTUUH6AocFxYuv5vOJAAAAHhJREFUKM+NzzEOQXEMB+DPYDY5iEVMIpzDfRxC3mZyBK7gChZnELGohaR58f7a7dd8bVq4YaVQgTvWFVjCUcXxA28qcBBHFUcVRwWPPuFfXVsbt0PPnLBL+dKHL+wxxhSPhBcZznuDXYKH1uGzBJ+YtPAZRyy/jTd7qEoydWUQ7QAAAABJRU5ErkJggg=="
CURSOR_BYTES = base64.b64decode(CURSOR_64)


genai.configure(api_key=os.environ["GEMINI_API_KEY"])

@dataclass
class Coordinate:
    """Represents a 2D coordinate."""

    x: int
    y: int


@dataclass
class ScrollBar:
    """Represents scrollbar metadata."""

    offset: float
    height: float


@dataclass
class BrowserState:
    """
    Holds the current state of a browser, including:
    - base64 encoded screenshot of the visible viewport
    - browser dimensions
    - scrollbar info
    - current URL
    - mouse coordinate
    """

    screenshot: str
    height: int
    width: int
    scrollbar: ScrollBar
    url: str
    mouse: Coordinate


@dataclass
class BrowserAction:
    """
    Represents a single action within the browser, e.g. mouse move, click, typing,
    scroll, etc.
    """

    action: Literal[
        "success",
        "failure",
        "key",
        "type",
        "mouse_move",
        "left_click",
        "left_click_drag",
        "right_click",
        "middle_click",
        "double_click",
        "screenshot",
        "cursor_position",
        "scroll_up",
        "scroll_down",
    ]
    coordinate: Tuple[int, int] | None
    text: str | None
    reasoning: str
    id: str


@dataclass
class BrowserStep:
    """
    Ties together the browser state with the action taken during that state.
    """

    state: BrowserState
    action: BrowserAction

class vLLMResponse(BaseModel):
    last_step_analysis: str
    is_last_step_successful: bool
    review_of_past_steps: str
    current_state: str
    current_mouse_analysis: str
    current_active_element: str
    potential_action_1: str
    potential_action_2: str
    potential_action_3: str
    potential_action_4: str
    potential_action_5: str
    potential_action_analysis: str
    next_action_plan: str


def backfill_reasoning(goal: str, steps: List[BrowserStep]):
    # For each step, update the screenshot to include mouse and scrollbar overlays
    for step in steps:
        # Get the browser state
        browser_state = step.state
        
        # Get mouse position and scrollbar info
        mouse_pos = Coordinate(x=math.floor(browser_state.mouse.x), y=math.floor(browser_state.mouse.y))
        scrollbar = browser_state.scrollbar
        
        # Convert base64 screenshot back to bytes
        img_bytes = base64.b64decode(browser_state.screenshot)
        print(mouse_pos)
        
        # Mark the screenshot with overlays
        marked_img_bytes = mark_screenshot(
            img_bytes,
            mouse_pos,
            scrollbar,
            None  # No active element highlighting needed for backfilling
        )
        
        # Convert back to base64 and update the browser state
        marked_b64 = base64.b64encode(marked_img_bytes).decode('utf-8')
        browser_state.screenshot = marked_b64

        # Normalize mouse coordinates to [0, 1000] based on viewport dimensions
        normalized_x = int((mouse_pos.x / browser_state.width) * 1000)
        normalized_y = int((mouse_pos.y / browser_state.height) * 1000)
        browser_state.mouse = Coordinate(x=normalized_x, y=normalized_y)
        print("AFTER", browser_state.mouse)
        print(asdict(step.action))


        if step.action.coordinate:
            # Extract original coordinates
            orig_x, orig_y = step.action.coordinate
            
            # Normalize coordinates to [0, 1000] based on viewport dimensions
            norm_x = int((orig_x / step.state.width) * 1000)
            norm_y = int((orig_y / step.state.height) * 1000)
            
            # Update the action coordinates
            step.action.coordinate = (norm_x, norm_y)

    last_action_taken = "Take a screenshot of the browser."
    past_action_history = "Browsing session started."

    model_1 = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0,
                "max_output_tokens": 1024,
                # "response_schema": content.Schema(
                #     type = content.Type.OBJECT,
                #     properties = {
                #     "last_step_analysis": content.Schema(
                #         type = content.Type.STRING,
                #     ),
                #     "is_last_step_successful": content.Schema(
                #         type = content.Type.BOOLEAN,
                #     ),
                #     },
                # ),
                "response_mime_type": "application/json",
                },
            )
    
    model_2 = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0,
                "max_output_tokens": 2000,
                # "response_schema": content.Schema(
                #     type = content.Type.OBJECT,
                #     properties = {
                #     "last_step_analysis": content.Schema(
                #         type = content.Type.STRING,
                #     ),
                #     "is_last_step_successful": content.Schema(
                #         type = content.Type.BOOLEAN,
                #     ),
                #     },
                # ),
                "response_mime_type": "application/json",
                },
            )

    for i in range(len(steps)):
        step = steps[i]
        last_attempt_prompt = f'''
You are being show a single user action step in a browsing session. Your task is to analyze the <LAST_ATTEMPTED_ACTION> and see if the action was successful. You are provided with:

* A screenshot of the browser after <LAST_ATTEMPTED_ACTION>
* A <PAST_ACTION_HISTORY> which describes the chain of actions taken before the <LAST_ATTEMPTED_ACTION>
* The <GOAL> of the user

<GOAL>
{goal}
</GOAL>

<LAST_ATTEMPTED_ACTION>
{last_action_taken}
</LAST_ATTEMPTED_ACTION>

<PAST_ACTION_HISTORY>
{past_action_history}
</PAST_ACTION_HISTORY>

Output a JSON in the following format:
{{
    last_step_analysis: str, # Concisely reason out if the LAST_ATTEMPTED_ACTION accomplished the desired outcome, for exaxmple, if the LAST_ATTEMPTED_ACTION was to take a screenshot and a screenshot was provided then this would be a success.
    is_last_step_successful: bool, # A boolean true or false
}}
'''
    
        response = model_1.generate_content([
                { 'mime_type':'image/jpeg', 'data': step.state.screenshot},
                last_attempt_prompt
            ])
        
        last_step_analysis = json.loads(response.text)

        print(json.dumps(last_step_analysis, indent=4))

        # Deep copy the action and remove specified fields
        action_copy = dataclasses.replace(step.action)
        action_dict = dataclasses.asdict(action_copy)
        action_dict.pop('reasoning', None)
        action_dict.pop('id', None)
        action_dict = {k:v for k,v in action_dict.items() if v is not None}

        next_step_backfill_prompt = f'''
You are being show a single user action step in a browsing session. Your task come up with the chain of thought that led the user to the next action in service of accomplishing their <GOAL>. You are provided with:

* The <GOAL> of the user
* A <NEXT_ACTION_INPUT> this is the mechanical operation of mouse or keyboard for the next action.
* A <LAST_ATTEMPTED_ACTION> which describes the the last attempted action.
* A <PAST_ACTION_HISTORY> which describes the chain of actions taken before the <LAST_ATTEMPTED_ACTION>.
* A screenshot of the browser after <LAST_ATTEMPTED_ACTION> but before <NEXT_ACTION_INPUT> is taken.

<GOAL>
{goal}
</GOAL>

<LAST_ATTEMPTED_ACTION>
{last_action_taken}

{last_step_analysis["last_step_analysis"]}
</LAST_ATTEMPTED_ACTION>

<PAST_ACTION_HISTORY>
{past_action_history}
</PAST_ACTION_HISTORY>

<NEXT_ACTION_INPUT>
{json.dumps(action_dict)}
</NEXT_ACTION_INPUT>

Output a JSON in the following format:
{{
    review_of_past_steps: str,  # Synthesize <LAST_ATTEMPTED_ACTION> together with <PAST_ACTION_HISTORY> to summarize all prior attempted actions.
    current_state: str,         # Describe the current state of the webpage
    current_mouse_analysis: str, # Describe mouse cursor position relative to visible UI elements. Do not discuss the intent of the mouse position.
    current_active_element: str, # Identify which element currently has focus/is active
    next_action_plan: str        # Describe in words what the <NEXT_ACTION_INPUT> is attempting to do
    alternative_action_1: str,     # First alternative next action the user could take
    alternative_action_2: str,     # Second alternative next action the user could take  
    alternative_action_3: str,     # Third alternative next action the user could take
    alternative_action_4: str,     # Fourth alternative next action the user could take
    next_action_analysis: str, # Given you know the next_action_plan is the correct action to take, reason through why each of the alternative actions are inferior to the next_action_plan
}}
'''
    
        response_2 = model_2.generate_content([
                { 'mime_type':'image/jpeg', 'data': step.state.screenshot},
                next_step_backfill_prompt
            ])
    
        # Save screenshot to jpeg file
        screenshot_data = base64.b64decode(step.state.screenshot)
        screenshot_image = Image.open(BytesIO(screenshot_data))
        screenshot_image.save(f'step_{i}.jpeg')

        backfill = json.loads(response_2.text)

        last_action_taken = backfill["next_action_plan"]
        past_action_history = backfill["review_of_past_steps"]

        print(json.dumps(backfill, indent=4))

    return []


def generate_tool_id() -> str:
    """
    Generates a pseudo-random string ID for a browser action.
    """
    prefix = "toolu_01"
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    id_length = 22
    result = prefix
    for _ in range(id_length):
        result += random.choice(characters)
    return result


def is_in_viewport(
    viewport: Tuple[float, float, float, float], point: Tuple[float, float]
) -> bool:
    """
    Checks if the given point is within the specified viewport.

    Args:
        viewport: (x1, y1, x2, y2)
        point: (x, y)

    Returns:
        bool: True if the point is within the viewport, else False.
    """
    x1, y1, x2, y2 = viewport
    x, y = point
    return x1 <= x <= x2 and y1 <= y <= y2


def scroll_viewport(
    direction: str, viewport: Tuple[float, float, float, float], y_max: float
) -> Tuple[float, float, float, float]:
    """
    Scrolls the viewport either up or down.

    Args:
        direction: Either 'up' or 'down'.
        viewport: The current (x1, y1, x2, y2) representing the viewport.
        y_max: The maximum Y dimension of the screenshot.

    Returns:
        A new (x1, y1, x2, y2) for the updated viewport.
    """
    x1, y1, x2, y2 = viewport
    height = y2 - y1
    scroll_amount = 0.75 * height

    if direction == "up":
        new_y1 = max(1, y1 - scroll_amount)
        new_y2 = new_y1 + height
    elif direction == "down":
        new_y2 = min(y_max, y2 + scroll_amount)
        new_y1 = new_y2 - height
    else:
        raise ValueError("Direction must be 'up' or 'down'")

    # Adjust if the new viewport exceeds bounds while preserving height
    if new_y1 < 1:
        new_y1 = 1
        new_y2 = new_y1 + height
    if new_y2 > y_max:
        new_y2 = y_max
        new_y1 = new_y2 - height

    return (x1, new_y1, x2, new_y2)


def viewport_screenshot(
    screenshot: Image.Image, viewport: Tuple[float, float, float, float]) -> str:
    """
    Crops the given screenshot to the specified viewport and returns a base64 encoding
    of the cropped image.

    Args:
        screenshot: The original PIL Image.
        viewport: The (x1, y1, x2, y2) region to crop.

    Returns:
        Base64-encoded string of the cropped JPEG image.
    """
    x1, y1, x2, y2 = map(int, viewport)
    cropped_image = screenshot.copy().crop((x1, y1, x2, y2))

    buffered = BytesIO()
    cropped_image.save(buffered, format="JPEG", quality=85)
    encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_string

def mark_screenshot(img_buffer: bytes, mouse_position: Coordinate, scrollbar: ScrollBar, active_element: Union[tuple[Coordinate, Coordinate], None]
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
    with Image.open(BytesIO(img_buffer)) as img:
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
        cursor_img = Image.open(BytesIO(CURSOR_BYTES))
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
        output_buffer = BytesIO()
        composite.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

def process_step(
    step, mouse_coordinates: Coordinate
) -> Tuple[List[BrowserStep], Coordinate]:
    """
    Processes a single data record (step) to create a list of `BrowserStep` objects.
    It generates intermediate steps for scrolling, mouse movement, and clicking.

    Args:
        step: A dict-like object containing screenshot, pos_candidates, and operation info.
        mouse_coordinates: Current mouse coordinates.

    Returns:
        A tuple of (list of BrowserSteps, updated mouse coordinates).
    """
    cerebellum_steps: List[BrowserStep] = []

    # Initialize the viewport to the top 16:10 ratio part of the screenshot
    screenshot = step["screenshot"]
    width, height = screenshot.size
    viewport_height = width * 10 / 16
    viewport = (0, 0, width, viewport_height)

    # Find the bounding box of the first pos_candidates
    if len(step["pos_candidates"]) == 0:
        return ([], mouse_coordinates)

    candidate = json.loads(step["pos_candidates"][0])
    attributes = json.loads(candidate["attributes"])
    bounding_box_rect = attributes["bounding_box_rect"]
    x, y, box_width, box_height = map(float, bounding_box_rect.split(","))
    center_x = x + box_width / 2
    center_y = y + box_height / 2

    if not (0 <= center_x <= width and 0 <= center_y <= height):
        print("Bounding box coordinates outside of provided screenshot, skipping step")
        return ([], mouse_coordinates)

    y_max = float(height)
    # Scroll the viewport until the center of the bounding box is in view
    while not is_in_viewport(viewport, (center_x, center_y)):
        if center_y < viewport[1]:
            browser_state = BrowserState(
                url="",
                screenshot=viewport_screenshot(screenshot, viewport),
                height=viewport_height,
                width=width,
                scrollbar=ScrollBar(
                    offset=float(viewport[1]) / y_max,
                    height=float(viewport_height) / y_max,
                ),
                mouse=mouse_coordinates,
            )
            page_up_action = BrowserAction(
                action="key",
                coordinate=None,
                text="PAGE_UP",
                reasoning="Press the Page Up key to scroll up",
                id=generate_tool_id(),
            )
            cerebellum_steps.append(
                BrowserStep(state=browser_state, action=page_up_action)
            )
            viewport = scroll_viewport("up", viewport, y_max)

        elif center_y > viewport[3]:
            browser_state = BrowserState(
                url="",
                screenshot=viewport_screenshot(screenshot, viewport),
                height=viewport_height,
                width=width,
                scrollbar=ScrollBar(
                    offset=float(viewport[1]) / y_max,
                    height=float(viewport_height) / y_max,
                ),
                mouse=mouse_coordinates,
            )
            page_down_action = BrowserAction(
                action="key",
                coordinate=None,
                text="PAGE_DOWN",
                reasoning="Press the Page Down key to scroll down",
                id=generate_tool_id(),
            )
            cerebellum_steps.append(
                BrowserStep(state=browser_state, action=page_down_action)
            )
            viewport = scroll_viewport("down", viewport, y_max)

    # Create a mouse movement action to position the mouse in the center of the bounding box
    center_x_relative = center_x - viewport[0]
    center_y_relative = center_y - viewport[1]
    mouse_move_action = BrowserAction(
        action="mouse_move",
        coordinate=(center_x_relative, center_y_relative),
        text=None,
        reasoning="Move mouse to the center of the element",
        id=generate_tool_id(),
    )
    browser_state = BrowserState(
        url="",
        screenshot=viewport_screenshot(screenshot, viewport),
        height=viewport_height,
        width=width,
        scrollbar=ScrollBar(
            offset=float(viewport[1]) / y_max,
            height=float(viewport_height) / y_max,
        ),
        mouse=mouse_coordinates,
    )
    move_step = BrowserStep(state=browser_state, action=mouse_move_action)
    cerebellum_steps.append(move_step)

    # Update the mouse coordinates after the move
    mouse_coordinates = Coordinate(x=center_x_relative, y=center_y_relative)

    # Perform a left click action
    left_click_action = BrowserAction(
        action="left_click",
        coordinate=None,
        text=None,
        reasoning="Perform a left click on element",
        id=generate_tool_id(),
    )
    browser_state = BrowserState(
        url="",
        screenshot=viewport_screenshot(screenshot, viewport),
        height=viewport_height,
        width=width,
        scrollbar=ScrollBar(
            offset=float(viewport[1]) / y_max,
            height=float(viewport_height) / y_max,
        ),
        mouse=mouse_coordinates,
    )
    left_click_step = BrowserStep(state=browser_state, action=left_click_action)
    cerebellum_steps.append(left_click_step)

    # Create corresponding key actions if the step operation is "TYPE" or "SELECT"
    operation = json.loads(step["operation"])
    if operation["op"] in ["TYPE", "SELECT"]:
        text = operation["value"]
        type_action = BrowserAction(
            action="type",
            coordinate=None,
            text=text,
            reasoning="Typing text set to desired value",
            id=generate_tool_id(),
        )
        browser_state = BrowserState(
            url="",
            screenshot=viewport_screenshot(screenshot, viewport),
            height=viewport_height,
            width=width,
            scrollbar=ScrollBar(
                offset=float(viewport[1]) / y_max,
                height=float(viewport_height) / y_max,
            ),
            mouse=mouse_coordinates,
        )
        type_step = BrowserStep(state=browser_state, action=type_action)
        cerebellum_steps.append(type_step)

    return (cerebellum_steps, mouse_coordinates)


def main():
    parser = argparse.ArgumentParser(
        description="Process Mind2Web data to JSONL steps."
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="osunlp/Multimodal-Mind2Web",
        help="Name/path of the dataset to load (default: osunlp/Multimodal-Mind2Web).",
    )
    parser.add_argument(
        "--subset",
        type=str,
        default="train",
        help="Subset of the dataset to process (default: train).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="mind2web",
        help="Directory where JSONL files will be written (default: mind2web).",
    )
    args = parser.parse_args()

    # Load the dataset and select the subset
    ds = load_dataset(args.dataset_name)
    data_subset = ds.get(args.subset)

    # Create an iterator
    data_iterator = iter(data_subset)

    # Attempt to read the first record (if any)
    try:
        data_point = next(data_iterator)
    except StopIteration:
        print(
            f"No data found in subset '{args.subset}' for dataset '{args.dataset_name}'."
        )
        return

    # Optional: check keys for reference
    print("Data keys:", list(data_point.keys()))

    while True:
        # Each data_point belongs to a 'task'
        goal = data_point["confirmed_task"]
        task_id = data_point["annotation_id"]

        print("Grabbing steps for:", goal, task_id)
        steps = [data_point]

        # Keep pulling from the iterator until we get all steps for this goal
        while True:
            try:
                data_point = next(data_iterator)
            except StopIteration:
                data_iterator = None
                break

            if data_point["confirmed_task"] != goal:
                # This belongs to a new task; we'll handle it in the next iteration
                break
            steps.append(data_point)

        # Decompose each step into multiple browser steps
        cerebellum_steps: List[BrowserStep] = []
        mouse = Coordinate(x=5, y=5)
        for raw_step in steps:
            decomposed_steps, mouse = process_step(raw_step, mouse)
            cerebellum_steps += decomposed_steps

        # Backfill the reasoning for each cerebellum_step
        backfill_reasoning(goal, cerebellum_steps)

        # Define the output file path
        output_file_path = f"{args.output_dir}/{task_id}.jsonl"

        # Write the results
        with open(output_file_path, "w") as outfile:
            # Write the goal JSON
            goal_json = json.dumps({"goal": goal})
            outfile.write(goal_json + "\n")

            # Write each cerebellum step
            for this_step in cerebellum_steps:
                step_str = json.dumps(dataclasses.asdict(this_step))
                outfile.write(step_str + "\n")

        if not data_iterator:
            # If we've exhausted the dataset, break
            break


if __name__ == "__main__":
    main()
