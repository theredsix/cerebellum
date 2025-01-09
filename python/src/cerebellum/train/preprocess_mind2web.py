"""
Example usage:
--------------
python preprocess_mind2web.py --dataset_name osunlp/Multimodal-Mind2Web --subset train --output_dir mind2web
--------------

This script processes Mind2Web dataset browser interactions into discrete steps.
"""

import argparse
import base64
import json
import math
import os
import random
import dataclasses
from dataclasses import asdict, dataclass
from io import BytesIO
from typing import List, Optional, Tuple

import google.generativeai as genai
from cerebellum.browser import (
    BrowserAction,
    BrowserActionType,
    BrowserState,
    BrowserStep,
    BrowserTab,
    Coordinate,
    ScrollBar,
)
from cerebellum.planners.anthropic import CURSOR_64
from datasets import load_dataset
from PIL import Image, ImageDraw

# Base64 encoded cursor image
CURSOR_BYTES = base64.b64decode(CURSOR_64)


@dataclass
class ViewportDimensions:
    """Represents viewport dimensions and coordinates"""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Check if point is within viewport"""
        x, y = point
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


class ViewportManager:
    """Manages viewport positioning and screenshots"""

    def __init__(self, screenshot: Image.Image):
        self.screenshot = screenshot
        self.width, self.height = screenshot.size
        viewport_height = self.width * 10 / 16
        self.viewport = ViewportDimensions(0, 0, self.width, viewport_height)

    def scroll_viewport(self, direction: str) -> None:
        """Scrolls viewport up or down"""
        scroll_amount = 0.75 * self.viewport.height

        if direction == "up":
            new_y1 = max(1, self.viewport.y1 - scroll_amount)
            new_y2 = new_y1 + self.viewport.height
        elif direction == "down":
            new_y2 = min(self.height, self.viewport.y2 + scroll_amount)
            new_y1 = new_y2 - self.viewport.height
        else:
            raise ValueError("Direction must be 'up' or 'down'")

        if new_y1 < 1:
            new_y1 = 1
            new_y2 = new_y1 + self.viewport.height
        if new_y2 > self.height:
            new_y2 = self.height
            new_y1 = new_y2 - self.viewport.height

        self.viewport = ViewportDimensions(
            self.viewport.x1, new_y1, self.viewport.x2, new_y2
        )

    def get_screenshot(self) -> str:
        """Returns base64 encoded screenshot of current viewport"""
        cropped = self.screenshot.crop(
            (self.viewport.x1, self.viewport.y1, self.viewport.x2, self.viewport.y2)
        )
        buffered = BytesIO()
        cropped.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")


def generate_tool_id() -> str:
    """Generates a pseudo-random string ID for a browser action."""
    prefix = "toolu_01"
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    id_length = 22
    return prefix + "".join(random.choice(characters) for _ in range(id_length))


def mark_screenshot(
    img_buffer: bytes,
    mouse_position: Coordinate,
    scrollbar: ScrollBar,
    active_element: Optional[Tuple[Coordinate, Coordinate]] = None,
) -> bytes:
    """Adds scrollbar and cursor overlays to a screenshot."""
    with Image.open(BytesIO(img_buffer)) as img:
        width, height = img.size

        # Create scrollbar overlay
        scrollbar_width = 10
        scrollbar_height = int(height * scrollbar.height)
        scrollbar_top = int(height * scrollbar.offset)
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

        # Draw bounding box for active element
        if active_element:
            draw = ImageDraw.Draw(composite)
            top_left, dimensions = active_element

            x1 = max(0, min(top_left.x, width))
            y1 = max(0, min(top_left.y, height))
            x2 = max(0, min(top_left.x + dimensions.x, width))
            y2 = max(0, min(top_left.y + dimensions.y, height))

            draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=2, fill=None)

        output_buffer = BytesIO()
        composite.save(output_buffer, format="PNG")
        return output_buffer.getvalue()


def create_browser_state(
    screenshot: str,
    viewport_height: float,
    width: float,
    viewport_offset: float,
    mouse_coordinates: Coordinate,
) -> BrowserState:
    """Creates a BrowserState instance with given parameters"""
    return BrowserState(
        screenshot=screenshot,
        height=viewport_height,
        width=width,
        scrollbar=ScrollBar(
            offset=viewport_offset,
            height=viewport_height / width,
        ),
        tabs=[
            BrowserTab(handle="main", url="", title="", active=True, new=False, id=0)
        ],
        active_tab="main",
        mouse=mouse_coordinates,
    )


def process_step(
    step: dict, mouse_coordinates: Coordinate
) -> Tuple[List[BrowserStep], Coordinate]:
    """Processes a single data record into a list of BrowserStep objects."""
    if not step["pos_candidates"]:
        return [], mouse_coordinates

    # Initialize viewport manager
    viewport_mgr = ViewportManager(step["screenshot"])

    # Parse target element position
    candidate = json.loads(step["pos_candidates"][0])
    attributes = json.loads(candidate["attributes"])
    x, y, box_width, box_height = map(float, attributes["bounding_box_rect"].split(","))
    target_center = (x + box_width / 2, y + box_height / 2)

    if not (
        0 <= target_center[0] <= viewport_mgr.width
        and 0 <= target_center[1] <= viewport_mgr.height
    ):
        return [], mouse_coordinates

    cerebellum_steps: List[BrowserStep] = []

    # Scroll until target is visible
    while not viewport_mgr.viewport.contains_point(target_center):
        browser_state = create_browser_state(
            viewport_mgr.get_screenshot(),
            viewport_mgr.viewport.height,
            viewport_mgr.width,
            viewport_mgr.viewport.y1 / viewport_mgr.height,
            mouse_coordinates,
        )

        if target_center[1] < viewport_mgr.viewport.y1:
            action = BrowserAction(
                action=BrowserActionType.KEY,
                coordinate=None,
                text="PAGE_UP",
                reasoning="Press the Page Up key to scroll up",
                id=generate_tool_id(),
            )
            viewport_mgr.scroll_viewport("up")
        else:
            action = BrowserAction(
                action=BrowserActionType.KEY,
                coordinate=None,
                text="PAGE_DOWN",
                reasoning="Press the Page Down key to scroll down",
                id=generate_tool_id(),
            )
            viewport_mgr.scroll_viewport("down")

        cerebellum_steps.append(BrowserStep(state=browser_state, action=action))

    # Create mouse movement action
    target_x = target_center[0] - viewport_mgr.viewport.x1
    target_y = target_center[1] - viewport_mgr.viewport.y1

    browser_state = create_browser_state(
        viewport_mgr.get_screenshot(),
        viewport_mgr.viewport.height,
        viewport_mgr.width,
        viewport_mgr.viewport.y1 / viewport_mgr.height,
        mouse_coordinates,
    )

    mouse_move = BrowserAction(
        action=BrowserActionType.MOUSE_MOVE,
        coordinate=Coordinate(x=target_x, y=target_y),
        text=None,
        reasoning="Move mouse to the center of the element",
        id=generate_tool_id(),
    )

    cerebellum_steps.append(BrowserStep(state=browser_state, action=mouse_move))

    # Update mouse coordinates after move
    mouse_coordinates = Coordinate(x=target_x, y=target_y)

    # Perform click
    browser_state = create_browser_state(
        viewport_mgr.get_screenshot(),
        viewport_mgr.viewport.height,
        viewport_mgr.width,
        viewport_mgr.viewport.y1 / viewport_mgr.height,
        mouse_coordinates,
    )

    click = BrowserAction(
        action=BrowserActionType.LEFT_CLICK,
        coordinate=None,
        text=None,
        reasoning="Perform a left click on element",
        id=generate_tool_id(),
    )

    cerebellum_steps.append(BrowserStep(state=browser_state, action=click))

    # Handle typing if needed
    operation = json.loads(step["operation"])
    if operation["op"] in ["TYPE", "SELECT"]:
        browser_state = create_browser_state(
            viewport_mgr.get_screenshot(),
            viewport_mgr.viewport.height,
            viewport_mgr.width,
            viewport_mgr.viewport.y1 / viewport_mgr.height,
            mouse_coordinates,
        )

        type_action = BrowserAction(
            action=BrowserActionType.TYPE,
            coordinate=None,
            text=operation["value"],
            reasoning="Typing text set to desired value",
            id=generate_tool_id(),
        )

        cerebellum_steps.append(BrowserStep(state=browser_state, action=type_action))

    return cerebellum_steps, mouse_coordinates


def backfill_reasoning(goal: str, steps: List[BrowserStep]) -> None:
    """Analyzes each step and backfills reasoning using Gemini API."""
    # Initialize Gemini
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    model_1 = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "temperature": 0,
            "max_output_tokens": 1024,
            "response_mime_type": "application/json",
        },
    )

    model_2 = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "temperature": 0,
            "max_output_tokens": 2000,
            "response_mime_type": "application/json",
        },
    )

    last_action_taken = "Take a screenshot of the browser."
    past_action_history = "Browsing session started."

    # Process each step
    for i, step in enumerate(steps):
        # Update screenshots with overlays
        browser_state = step.state
        mouse_pos = Coordinate(
            x=math.floor(browser_state.mouse.x), y=math.floor(browser_state.mouse.y)
        )

        img_bytes = base64.b64decode(browser_state.screenshot)
        marked_img_bytes = mark_screenshot(
            img_bytes, mouse_pos, browser_state.scrollbar
        )
        marked_b64 = base64.b64encode(marked_img_bytes).decode("utf-8")

        # Create new state with updated screenshot
        new_state = BrowserState(
            screenshot=marked_b64,
            height=browser_state.height,
            width=browser_state.width,
            scrollbar=browser_state.scrollbar,
            tabs=browser_state.tabs,
            active_tab=browser_state.active_tab,
            mouse=Coordinate(
                x=int((mouse_pos.x / browser_state.width) * 1000),
                y=int((mouse_pos.y / browser_state.height) * 1000),
            ),
        )
        steps[i] = dataclasses.replace(step, state=new_state)

        # For coordinate normalization
        if step.action.coordinate:
            orig_x, orig_y = step.action.coordinate.x, step.action.coordinate.y
            new_action = BrowserAction(
                action=step.action.action,
                coordinate=Coordinate(
                    x=int((orig_x / step.state.width) * 1000),
                    y=int((orig_y / step.state.height) * 1000),
                ),
                text=step.action.text,
                reasoning=step.action.reasoning,
                id=step.action.id,
            )
            steps[i] = dataclasses.replace(steps[i], action=new_action)

        # Generate reasoning for last action
        last_attempt_prompt = f"""
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
    last_step_analysis: str, # Concisely reason out if the LAST_ATTEMPTED_ACTION accomplished the desired outcome
    is_last_step_successful: bool, # A boolean true or false
}}
"""

        response = model_1.generate_content(
            [
                {"mime_type": "image/jpeg", "data": step.state.screenshot},
                last_attempt_prompt,
            ]
        )

        last_step_analysis = json.loads(response.text)

        # Create copy of action for analysis
        action_dict = asdict(step.action)
        action_dict.pop("reasoning", None)
        action_dict.pop("id", None)
        action_dict = {k: v for k, v in action_dict.items() if v is not None}

        # Generate reasoning for next action
        next_step_prompt = f"""
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
    review_of_past_steps: str,  # Synthesize all prior attempted actions
    current_state: str,         # Describe the current state of the webpage
    current_mouse_analysis: str, # Describe mouse cursor position relative to visible UI elements
    current_active_element: str, # Identify which element currently has focus/is active
    next_action_plan: str,      # Describe in words what the <NEXT_ACTION_INPUT> is attempting to do
    alternative_action_1: str,   # First alternative next action the user could take
    alternative_action_2: str,   # Second alternative next action the user could take  
    alternative_action_3: str,   # Third alternative next action the user could take
    alternative_action_4: str,   # Fourth alternative next action the user could take
    next_action_analysis: str,   # Reason through why alternatives are inferior to the next_action_plan
}}
"""

        response_2 = model_2.generate_content(
            [
                {"mime_type": "image/jpeg", "data": step.state.screenshot},
                next_step_prompt,
            ]
        )

        backfill = json.loads(response_2.text)
        last_action_taken = backfill["next_action_plan"]
        past_action_history = backfill["review_of_past_steps"]


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process Mind2Web data to JSONL steps."
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="osunlp/Multimodal-Mind2Web",
        help="Name/path of the dataset to load.",
    )
    parser.add_argument(
        "--subset",
        type=str,
        default="train",
        help="Subset of the dataset to process.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="mind2web",
        help="Directory where JSONL files will be written.",
    )
    args = parser.parse_args()

    # Load dataset
    ds = load_dataset(args.dataset_name)
    data_subset = ds.get(args.subset)

    if not data_subset:
        print(
            f"No data found in subset '{args.subset}' for dataset '{args.dataset_name}'."
        )
        return

    data_iterator = iter(data_subset)
    data_point = next(data_iterator, None)

    while data_point:
        goal = data_point["confirmed_task"]
        task_id = data_point["annotation_id"]

        # Collect all steps for current task
        steps = [data_point]
        while True:
            data_point = next(data_iterator, None)
            if not data_point or data_point["confirmed_task"] != goal:
                break
            steps.append(data_point)

        # Process steps
        cerebellum_steps: List[BrowserStep] = []
        mouse = Coordinate(x=5, y=5)

        for raw_step in steps:
            decomposed_steps, mouse = process_step(raw_step, mouse)
            cerebellum_steps.extend(decomposed_steps)

        # Backfill reasoning
        # backfill_reasoning(goal, cerebellum_steps)

        # Write output
        output_file = os.path.join(args.output_dir, f"{task_id}.jsonl")
        with open(output_file, "w") as f:
            f.write(json.dumps({"goal": goal}) + "\n")
            for step in cerebellum_steps:
                f.write(json.dumps(asdict(step)) + "\n")


if __name__ == "__main__":
    main()
