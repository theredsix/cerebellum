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
import random
from dataclasses import dataclass, asdict
from io import BytesIO
from typing import List, Literal, Tuple

from datasets import load_dataset
from PIL import Image

from pydantic import BaseModel
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import os


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
    last_action_taken = "Take a screenshot of the browser."
    past_action_history = "Browsing session started."

    model_1 = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config={
                "temperature": 1,
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
                "temperature": 1,
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
{json.dumps(asdict(step.action))}
</NEXT_ACTION_INPUT>

Output a JSON in the following format:
{{
    review_of_past_steps: str,  # Synthesize <LAST_ATTEMPTED_ACTION> together with <PAST_ACTION_HISTORY> to summarize all prior attempted actions.
    current_state: str,         # Describe the current state of the webpage
    current_mouse_analysis: str, # State where the mouse cursor is on the screen. Do not output an exact coordinate but describe where it is relative to other visible major UI elements.
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
    screenshot: Image.Image, viewport: Tuple[float, float, float, float]
) -> str:
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
        mouse = Coordinate(x=1, y=1)
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
