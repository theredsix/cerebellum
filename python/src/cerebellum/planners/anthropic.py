"""Anthropic planner module for browser automation.

This module provides the AnthropicPlanner class which uses Anthropic's Claude API
to control browser actions. It handles screenshot analysis, coordinate transformations,
and maintains browser state.

Typical usage example:

    planner = AnthropicPlanner(api_key="key123")
    action = planner.plan_action(goal="Click login button", 
                               current_state=browser_state)
"""

import base64
import io
import json
import random
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from math import floor
from typing import Any, cast

from anthropic import Anthropic
from anthropic.types.beta import (
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlockParam,
)
from cerebellum.browser import (
    ActionPlanner,
    BrowserAction,
    BrowserState,
    BrowserStep,
    Coordinate,
    ScrollBar,
)
from PIL import Image


@dataclass(frozen=True)
class ScalingRatio:
    ratio_x: float
    ratio_y: float
    old_size: Coordinate
    new_size: Coordinate


@dataclass(frozen=False)
class MsgOptions:
    mouse_position: bool
    screenshot: bool
    url: bool


# Base64 encoded cursor image
CURSOR_64 = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAQCAYAAAAvf+5AAAAAw3pUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjabVBRDsMgCP33FDuC8ijF49i1S3aDHX9YcLFLX+ITeOSJpOPzfqVHBxVOvKwqVSQbuHKlZoFmRzu5ZD55rvX8Uk9Dz2Ql2A1PVaJ/1MvPwK9m0TIZ6TOE7SpUDn/9M4qH0CciC/YwqmEEcqGEQYsvSNV1/sJ25CvUTxqBjzGJU86rbW9f7B0QHSjIxoD6AOiHE1oXjAlqjQVyxmTMkJjEFnK3p4H0BSRiWUv/cuYLAAABhWlDQ1BJQ0MgcHJvZmlsZQAAeJx9kT1Iw0AYht+2SqVUHCwo0iFD1cWCqIijVqEIFUKt0KqDyaV/0KQhSXFxFFwLDv4sVh1cnHV1cBUEwR8QZwcnRRcp8buk0CLGg7t7eO97X+6+A/yNClPNrnFA1SwjnUwI2dyqEHxFCFEM0DoqMVOfE8UUPMfXPXx8v4vzLO+6P0evkjcZ4BOIZ5luWMQbxNObls55nzjCSpJCfE48ZtAFiR+5Lrv8xrnosJ9nRoxMep44QiwUO1juYFYyVOIp4piiapTvz7qscN7irFZqrHVP/sJwXltZ5jrNKJJYxBJECJBRQxkVWIjTrpFiIk3nCQ//kOMXySWTqwxGjgVUoUJy/OB/8Lu3ZmFywk0KJ4DuF9v+GAaCu0Czbtvfx7bdPAECz8CV1vZXG8DMJ+n1thY7Avq2gYvrtibvAZc7wOCTLhmSIwVo+gsF4P2MvikH9N8CoTW3b61znD4AGepV6gY4OARGipS97vHuns6+/VvT6t8Ph1lyr0hzlCAAAA14aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOjFiYzFkZjE3LWM5YmMtNGYzZi1hMmEzLTlmODkyNWNiZjY4OSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo4YTUyMWJhMC00YmNlLTQzZWEtYjgyYS04ZGM2MTBjYmZlOTgiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplODQ3ZjUxNC00MWVlLTQ2ZjYtOTllNC1kNjI3MjMxMjhlZTIiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE3MzAxNTc3NjY5MTI3ODciCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zOCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQ6MTA6MjhUMTY6MjI6NDYtMDc6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDI0OjEwOjI4VDE2OjIyOjQ2LTA3OjAwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZTVjOTM2ZDYtYjMzYi00NzM4LTlhNWUtYjM3YTA5MzdjZDAxIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyNC0xMC0yOFQxNjoyMjo0Ni0wNzowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz5/5aQ8AAAABmJLR0QAcgByAAAtJLTuAAAACXBIWXMAAABZAAAAWQGqnamGAAAAB3RJTUUH6AocFxYuv5vOJAAAAHhJREFUKM+NzzEOQXEMB+DPYDY5iEVMIpzDfRxC3mZyBK7gChZnELGohaR58f7a7dd8bVq4YaVQgTvWFVjCUcXxA28qcBBHFUcVRwWPPuFfXVsbt0PPnLBL+dKHL+wxxhSPhBcZznuDXYKH1uGzBJ+YtPAZRyy/jTd7qEoydWUQ7QAAAABJRU5ErkJggg=="
CURSOR_BYTES = base64.b64decode(CURSOR_64)


@dataclass(frozen=True)
class AnthropicPlannerOptions:
    """Configuration options for the Anthropic planner.

    Args:
        screenshot_history: Number of previous screenshots to include in context.
        mouse_jitter_reduction: Pixel threshold for mouse movement jitter reduction.
        api_key: Anthropic API key for authentication.
        client: Pre-configured Anthropic client instance.
        debug_image_path: Path to save debug images.
    """

    screenshot_history: int | None = None
    mouse_jitter_reduction: int | None = None
    api_key: str | None = None
    client: Anthropic | None = None
    debug_image_path: str | None = None


class AnthropicPlanner(ActionPlanner):
    """A planner that uses Anthropic's Claude API to control browser actions.

    This planner interfaces with Claude to interpret browser state and determine
    appropriate actions to achieve user goals. It handles screenshot analysis,
    mouse movements, keyboard input, and maintains context of the browsing session.

    Attributes:
        client: The Anthropic API client instance
        screenshot_history: Number of previous screenshots to include in context
        mouse_jitter_reduction: Pixel threshold for reducing mouse movement jitter
        input_token_usage: Count of tokens used in API requests
        output_token_usage: Count of tokens used in API responses
        debug_image_path: Optional path to save debug screenshots
        debug: Whether debug mode is enabled
    """

    def __init__(self, options: AnthropicPlannerOptions | None = None) -> None:
        """Initializes the Anthropic planner.

        Args:
            options: Configuration options for the planner. If None, uses defaults.
        """
        super().__init__()

        self.client: Anthropic
        if options and options.client:
            self.client = options.client
        elif options and options.api_key:
            self.client = Anthropic(api_key=options.api_key)
        else:
            self.client = Anthropic()

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
        self.debug_image_path: str | None = (
            options.debug_image_path if options else None
        )
        self.debug: bool = False

    def format_system_prompt(
        self, goal: str, additional_context: str, additional_instructions: list[str]
    ) -> str:
        """Formats the system prompt for the Anthropic model.

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
* Since the browser is in fullscreen mode, you do not have access to browser UI elements such as STOP, REFRESH, BACK or the address bar. You will need to complete your task purely by interacting with the webside's UI.
* Scroll down to see everything before deciding something isn't available.
* ONLY use the Page_down or Page_up keys to scroll.
* If the website is scrollable, a scrollbar that is shaped like a gray rectangle will be visible on the right edge of the screenshot.
* The current date is {datetime.now().isoformat()}.
* Follow all directions from the <IMPORTANT> section below. 
* The mouse cursor is present in the screenshot.
</SYSTEM_CAPABILITY>

The user will ask you to perform a task and you should use their browser to do so. After each step, take a screenshot and carefully evaluate if you have achieved the right outcome. Explicitly show your thinking for EACH function call: "I have evaluated step X..." If not correct, try again. Only when you confirm a step was executed correctly should you move on to the next one. You should always call a tool! Always return a tool call. Remember call the stop_browsing tool when you have achieved the goal of the task. Use keyboard shortcuts to navigate whenever possible.

<IMPORTANT>
* ALWAYS left_click after a mouse move once the mouse cursor is hovering over the correct location.
* You will use information provided in user's <USER DATA> to fill out forms on the way to your goal.
* Always scroll a UI element fully into view before interacting with it.
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
        self, img_buffer: bytes, mouse_position: Coordinate, scrollbar: ScrollBar
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
        1280x800 while maintaining the aspect ratio. The ratio is original size / new size.
        To get the new size from the ratio, multiply the original size by the inverse of
        the ratio, or simply divide the original size by the ratio. To go from the new size
        back to the original size, multiply the new size by the ratio.

        Args:
            orig_size: Coordinate object containing original width and height

        Returns:
            ScalingRatio object containing scale factors and dimensions
        """
        aspect_ratio = orig_size.x / orig_size.y

        if aspect_ratio > 1280 / 800:
            new_width = 1280
            new_height = floor(1280 / aspect_ratio)
        else:
            new_height = 800
            new_width = floor(800 * aspect_ratio)

        width_ratio = orig_size.x / new_width
        height_ratio = orig_size.y / new_height

        return ScalingRatio(
            ratio_x=width_ratio,
            ratio_y=height_ratio,
            old_size=orig_size,
            new_size=Coordinate(x=new_width, y=new_height),
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
    ) -> BetaMessageParam:
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
        content_sub_msg: list[BetaTextBlockParam | BetaImageBlockParam] = []

        if options.mouse_position:
            img_dim = Coordinate(x=current_state.width, y=current_state.height)
            scaling = self.get_scaling_ratio(img_dim)
            scaled_coord = self.browser_to_llm_coordinates(current_state.mouse, scaling)
            result_text += f"After action mouse cursor is at X: {scaled_coord.x}, Y: {scaled_coord.y}\n\n"

        if options.url:
            result_text += f"After action, the tab's URL is {current_state.url}\n\n"

        if options.screenshot:
            result_text += "Here is a screenshot of the browser after the action was performed.\n\n"
            img_buffer = base64.b64decode(current_state.screenshot)
            viewport_image = self.resize_image_to_dimensions(
                img_buffer, Coordinate(x=current_state.width, y=current_state.height)
            )
            marked_image = self.mark_screenshot(
                viewport_image, current_state.mouse, current_state.scrollbar
            )
            resized = self.resize_screenshot(marked_image)

            if self.debug_image_path:
                with open(self.debug_image_path, "wb") as f:
                    f.write(resized)

            content_sub_msg.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(resized).decode(),
                    },
                }
            )

        if not result_text:  # Put a generic text explanation for no URL or result
            result_text = "Action was performed."

        content_sub_msg.insert(0, {"type": "text", "text": result_text.strip()})

        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": content_sub_msg,
                }
            ],
        }

    def format_into_messages(
        self,
        goal: str,
        additional_context: str,
        current_state: BrowserState,
        session_history: list[BrowserStep],
    ) -> list[BetaMessageParam]:
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
        messages: list[BetaMessageParam] = []
        tool_id = self.create_tool_use_id()

        user_prompt = f"""Please complete the following task:
<USER_TASK>
{goal}
</USER_TASK>

Using the supporting contextual data:
<USER_DATA>
{additional_context}
</USER_DATA>"""

        msg0: BetaMessageParam = {
            "role": "user",
            "content": [{"type": "text", "text": user_prompt.strip()}],
        }
        msg1: BetaMessageParam = {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Grab a view of the browser to understand what is the starting website state.",
                },
                {
                    "type": "tool_use",
                    "id": tool_id,
                    "name": "computer",
                    "input": {
                        "action": "screenshot",
                    },
                },
            ],
        }
        messages.extend([msg0, msg1])

        for past_step_idx, past_step in enumerate(session_history):
            options = MsgOptions(mouse_position=False, screenshot=False, url=True)

            if past_step_idx <= (len(session_history) - self.screenshot_history):
                options.url = True  # Matches TypeScript: options.url = true

            result_msg = self.format_state_into_msg(tool_id, past_step.state, options)
            messages.append(result_msg)

            # Update tool ID for next action
            tool_id = past_step.action.id or self.create_tool_use_id()

            inner_content = []

            inner_content.append(
                {
                    "type": "tool_use",
                    "id": tool_id,
                    "name": "computer",
                    "input": self.flatten_browser_step_to_action(past_step),
                }
            )

            action_msg: BetaMessageParam = {
                "role": "assistant",
                "content": inner_content,
            }
            messages.append(action_msg)

        current_state_message = self.format_state_into_msg(
            tool_id,
            current_state,
            MsgOptions(mouse_position=True, screenshot=True, url=True),
        )
        messages.append(current_state_message)

        return messages

    def parse_action(
        self, message: BetaMessage, scaling: ScalingRatio, current_state: BrowserState
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
        reasoning = " ".join(
            content.text for content in message.content if content.type == "text"
        )

        last_message = message.content[-1]

        print(last_message)
        if isinstance(last_message, str):
            return BrowserAction(
                action="failure",
                reasoning=last_message,
                coordinate=None,
                text=None,
                id=self.create_tool_use_id(),
            )

        if last_message.type != "tool_use":
            return BrowserAction(
                action="failure",
                reasoning=reasoning,
                text="Invalid message type",
                coordinate=None,
                id=self.create_tool_use_id(),
            )

        if last_message.name == "stop_browsing":
            input_data = cast(dict, last_message.input)
            if not input_data.get("success"):
                return BrowserAction(
                    action="failure",
                    reasoning=reasoning,
                    text=input_data.get("error", "Unknown error"),
                    coordinate=None,
                    id=last_message.id,
                )
            return BrowserAction(
                action="success",
                reasoning=reasoning,
                text=None,
                coordinate=None,
                id=last_message.id,
            )

        if last_message.name != "computer":
            return BrowserAction(
                action="failure",
                reasoning=reasoning,
                text="Wrong message called",
                coordinate=None,
                id=last_message.id,
            )

        input_data = cast(dict, last_message.input)
        action = input_data.get("action", "")
        coordinate: list[int] | None = input_data.get("coordinate")
        text = input_data.get("text")

        if isinstance(coordinate, str):
            print("Coordinate is a string:", coordinate)
            print(last_message)
            raw = json.loads(coordinate)
            if isinstance(raw, tuple):
                coordinate = raw
            elif isinstance(raw, dict):
                if "x" in raw and "y" in raw:
                    coordinate = (raw["x"], raw["y"])

        if isinstance(coordinate, dict):
            if "x" in coordinate and "y" in coordinate:
                print("Coordinate object has x and y properties")
                coordinate = (coordinate["x"], coordinate["y"])
            elif isinstance(coordinate, list):
                coordinate = (coordinate[0], coordinate[1])

        match action:
            case "key" | "type":
                if not text:
                    return BrowserAction(
                        action="failure",
                        reasoning=reasoning,
                        text=f"No text provided for {action}",
                        coordinate=None,
                        id=last_message.id,
                    )

                if action == "key":
                    # Handle special key mappings from utils.parse_xdotool
                    text_lower = text.lower().strip()
                    if text_lower in ("page_down", "pagedown"):
                        return BrowserAction(
                            action="scroll_down",
                            reasoning=reasoning,
                            coordinate=None,
                            text=None,
                            id=last_message.id,
                        )
                    if text_lower in ("page_up", "pageup"):
                        return BrowserAction(
                            action="scroll_up",
                            reasoning=reasoning,
                            coordinate=None,
                            text=None,
                            id=last_message.id,
                        )

                return BrowserAction(
                    action=action,
                    reasoning=reasoning,
                    text=text,
                    coordinate=None,
                    id=last_message.id,
                )

            case "mouse_move":
                if not coordinate:
                    return BrowserAction(
                        action="failure",
                        reasoning=reasoning,
                        text="No coordinate provided",
                        coordinate=None,
                        id=last_message.id,
                    )
                if isinstance(coordinate, str):
                    print(last_message)
                    return BrowserAction(
                        action="failure",
                        reasoning=reasoning,
                        text="Coordinate is a string, not array of integers.",
                        coordinate=None,
                        id=last_message.id,
                    )

                browser_coordinates = self.llm_to_browser_coordinates(
                    Coordinate(x=coordinate[0], y=coordinate[1]), scaling
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
                        action="left_click",
                        reasoning=reasoning,
                        coordinate=None,
                        text=None,
                        id=last_message.id,
                    )

                return BrowserAction(
                    action=action,
                    reasoning=reasoning,
                    coordinate=browser_coordinates,
                    text=None,
                    id=last_message.id,
                )

            case "left_click_drag":
                if not coordinate:
                    return BrowserAction(
                        action="failure",
                        reasoning=reasoning,
                        text="No coordinate provided",
                        coordinate=None,
                        id=last_message.id,
                    )

                browser_coordinates = self.llm_to_browser_coordinates(
                    Coordinate(x=coordinate[0], y=coordinate[1]), scaling
                )

                return BrowserAction(
                    action=action,
                    reasoning=reasoning,
                    coordinate=browser_coordinates,
                    text=None,
                    id=last_message.id,
                )

            case (
                "left_click"
                | "right_click"
                | "middle_click"
                | "double_click"
                | "screenshot"
                | "cursor_position"
            ):
                return BrowserAction(
                    action=action,
                    reasoning=reasoning,
                    coordinate=None,
                    text=None,
                    id=last_message.id,
                )

            case _:
                return BrowserAction(
                    action="failure",
                    reasoning=reasoning,
                    text=f"Unsupported computer action: {action}",
                    coordinate=None,
                    id=last_message.id,
                )

    def plan_action(
        self,
        goal: str,
        additional_context: str,
        additional_instructions: list[str],
        current_state: BrowserState,
        session_history: list[BrowserStep],
    ) -> BrowserAction:
        """Plans the next browser action based on the current state and goal.

        Uses the Anthropic Claude API to analyze the current browser state and determine
        the next action to take to achieve the specified goal.

        Args:
            goal: The task/goal to accomplish
            additional_context: Extra context information to help accomplish the goal
            additional_instructions: List of additional instructions to include
            current_state: Current state of the browser including coordinates and screenshot
            session_history: List of previous browser actions and their results

        Returns:
            A BrowserAction object containing the next action to take

        Raises:
            None
        """
        system_prompt = self.format_system_prompt(
            goal, additional_context, additional_instructions
        )
        messages = self.format_into_messages(
            goal, additional_context, current_state, session_history
        )

        self.print_messages_without_screenshots(messages)

        scaling = self.get_scaling_ratio(
            Coordinate(x=current_state.width, y=current_state.height)
        )

        response = self.client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            max_tokens=1024,
            tools=[
                {
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": current_state.width,
                    "display_height_px": current_state.height,
                    "display_number": 1,
                },
                {
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
            ],
            # tool_choice = {"type": "any"},
            messages=messages,
            betas=["computer-use-2024-10-22"],
        )

        print(
            f"Token usage - Input: {response.usage.input_tokens}, Output: {response.usage.output_tokens}"
        )
        self.input_token_usage += response.usage.input_tokens
        self.output_token_usage += response.usage.output_tokens
        print(
            f"Cumulative token usage - Input: {self.input_token_usage}, Output: {self.output_token_usage}, Total: {self.input_token_usage + self.output_token_usage}"
        )

        action = self.parse_action(response, scaling, current_state)
        print(action)

        return action

    def print_messages_without_screenshots(self, msg: list[BetaMessageParam]) -> None:
        """Prints messages after removing all screenshot image types."""

        msg_copy = deepcopy(msg)
        for message in msg_copy:
            if "content" in message:
                for outer_content in message["content"]:
                    if "content" in outer_content:
                        outer_content["content"] = [
                            content
                            for content in outer_content["content"]
                            if content["type"] != "image"
                        ]

        for message in msg_copy:
            print(json.dumps(message, indent=2))

    def flatten_browser_step_to_action(self, step: BrowserStep) -> Dict:
        if (step.action.action == 'scroll_down'):
            return {
                "action": "key",
                "text": "Page_Down"
            }
        
        if (step.action.action == 'scroll_up'):
            return {
                "action": "key",
                "text": "Page_Up"
            }
        
        val = {
            "action": step.action.action,
        }
        if step.action.text:
            val["text"] = step.action.text
        if step.action.coordinate:
            img_dim = Coordinate(x=step.state.width, y=step.state.height)
            scaling = self.get_scaling_ratio(img_dim)
            llm_coordinates = self.browser_to_llm_coordinates(
                step.action.coordinate, scaling
            )
            val["coordinate"] = [llm_coordinates.x, llm_coordinates.y]
        
        return val
