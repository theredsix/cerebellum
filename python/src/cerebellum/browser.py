"""Browser automation components for Cerebellum (python).

This module provides the core browser automation functionality: state management,
action planning, and action execution.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from cerebellum.utils import parse_xdotool, pause_for_input
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.remote.webdriver import WebDriver


class BrowserGoalState(StrEnum):
    """Enumeration of browser automation states.

    This enum represents the possible states of a browser automation task.

    Attributes:
        INITIAL: Starting state before automation begins
        RUNNING: Currently executing browser actions
        SUCCESS: Goal successfully achieved
        FAILED: Goal could not be achieved
    """

    INITIAL = "initial"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class Coordinate:
    """X & Y coordinates for mouse position or element location."""

    x: int
    y: int


@dataclass(frozen=True)
class BrowserViewportDimensions:
    """Dimensions for browser viewport or image size in pixels."""

    width: int
    height: int


@dataclass(frozen=True)
class ScrollBar:
    """Browser's scrollbar state."""

    offset: float
    height: float


@dataclass(frozen=True)
class BrowserState:
    """Comprehensive capture of browser state"""

    screenshot: str
    height: int
    width: int
    scrollbar: ScrollBar
    url: str
    mouse: Coordinate


@dataclass(frozen=True)
class BrowserAction:
    """An action to be performed on the browser."""

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
    ]
    coordinate: Coordinate | None
    text: str | None
    reasoning: str
    id: str


@dataclass(frozen=True)
class BrowserStep:
    """Single step for browser automation procedure."""

    state: BrowserState
    action: BrowserAction


class ActionPlanner(ABC):
    """Abstract base class for new action planners."""

    @abstractmethod
    def plan_action(
        self,
        goal: str,
        additional_context: str,
        additional_instructions: list[str],
        current_state: BrowserState,
        session_history: list[BrowserStep],
    ) -> BrowserAction:
        """Plan the next action from current state and step history.

        Args:
            goal (str): The goal to achieve.
            additional_context (str): Additional context for the planner.
            additional_instructions (list[str]): List of additional instructions.
            current_state (BrowserState): Current browser state.
            session_history (list[BrowserStep]): History of previous steps.

        Returns:
            BrowserAction: The next action to take.
        """
        pass


@dataclass(frozen=True)
class BrowserAgentOptions:
    """Wrapper for BrowserAgent additional configuration options."""

    additional_context: str | dict[str, Any] | None = None
    additional_instructions: list[str] | None = None
    wait_after_step_ms: int | None = None
    pause_after_each_action: bool | None = None
    max_steps: int | None = None


class BrowserAgent:
    """Main agent class for browser automation.

    This class coordinates between the WebDriver, action planner, and browser state
    to achieve specified goals through automated browser interactions.

    Args:
        driver: Selenium WebDriver instance
        action_planner: Planner implementation for determining actions
        goal: Goal to achieve
        options: Configuration options
    """

    def __init__(
        self,
        driver: WebDriver,
        action_planner: ActionPlanner,
        goal: str,
        options: BrowserAgentOptions | None = None,
    ) -> None:
        self.driver = driver
        self.planner = action_planner
        self.goal = goal
        self.additional_context = "None"
        self.additional_instructions: list[str] = []
        self.wait_after_step_ms = 500
        self.pause_after_each_action = False
        self.max_steps = 50
        self._status = BrowserGoalState.INITIAL
        self.history: list[BrowserStep] = []

        # Set options if supplied
        if options:
            if options.additional_context:
                if isinstance(options.additional_context, dict):
                    self.additional_context = json.dumps(options.additional_context)
                else:
                    self.additional_context = options.additional_context
            if options.additional_instructions:
                self.additional_instructions = options.additional_instructions
            if options.wait_after_step_ms:
                self.wait_after_step_ms = options.wait_after_step_ms
            if options.pause_after_each_action:
                self.pause_after_each_action = options.pause_after_each_action
            if options.max_steps:
                self.max_steps = options.max_steps

    def get_state(self) -> BrowserState:
        """Get current browser state."""
        viewport = self.driver.execute_script(
            "return { x: window.innerWidth, y: window.innerHeight }"
        )
        screenshot = self.driver.get_screenshot_as_base64()
        url = self.driver.current_url

        mouse_position = self.get_mouse_position()
        scroll_position = self.get_scroll_position()

        return BrowserState(
            screenshot=screenshot,
            height=viewport["y"],
            width=viewport["x"],
            scrollbar=scroll_position,
            url=url,
            mouse=mouse_position,
        )

    def get_action(self, current_state: BrowserState) -> BrowserAction:
        """Get next action from planner based on current state."""
        return self.planner.plan_action(
            self.goal,
            self.additional_context,
            self.additional_instructions,
            current_state,
            self.history,
        )

    def get_scroll_position(self) -> ScrollBar:
        """Get current scroll position information."""
        offset, height = self.driver.execute_script(
            "return [window.pageYOffset/document.documentElement.scrollHeight,"
            "window.innerHeight/document.documentElement.scrollHeight]"
        )
        return ScrollBar(offset=offset, height=height)

    def get_mouse_position(self) -> Coordinate:
        """Get current mouse cursor position."""
        script = """
        window.last_mouse_x = 0;
        window.last_mouse_y = 0;
        window.addEventListener('mousemove', function onMouseMove(ev) {
            window.last_mouse_x = ev.clientX;
            window.last_mouse_y = ev.clientY;
            window.removeEventListener('mousemove', onMouseMove);
        });
        """
        self.driver.execute_script(script)

        # Small mouse movement to trigger event
        actions = ActionChains(self.driver)
        actions.move_by_offset(3, 3).perform()
        actions.move_by_offset(-3, -3).perform()

        # Give time for event to register
        time.sleep(0.1)

        x, y = self.driver.execute_script(
            "return [window.last_mouse_x, window.last_mouse_y]"
        )

        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return Coordinate(x=int(x), y=int(y))

        return Coordinate(x=0, y=0)

    def take_action(self, action: BrowserAction, last_state: BrowserState) -> None:
        """Execute the specified browser action."""
        action_builder = ActionBuilder(self.driver)

        match action.action:
            case "key":
                if not action.text:
                    raise ValueError("Text is required for key action")

                key_strokes = parse_xdotool(action.text)

                for modifier in key_strokes.modifiers:
                    action_builder.key_action.key_down(modifier)
                for key in key_strokes.keys:
                    action_builder.key_action.send_keys(key)
                for modifier in reversed(key_strokes.modifiers):
                    action_builder.key_action.key_up(modifier)

                action_builder.perform()

            case "type":
                if not action.text:
                    raise ValueError("Text is required for type action")
                action_builder.key_action.send_keys(action.text)
                action_builder.perform()

            case "mouse_move":
                if not action.coordinate:
                    raise ValueError("Coordinate is required for mouse_move action")
                action_builder.pointer_action.move_to_location(
                    action.coordinate.x, action.coordinate.y
                )
                action_builder.perform()

            case "left_click":
                action_builder.pointer_action.click()
                action_builder.perform()

            case "left_click_drag":
                if not action.coordinate:
                    raise ValueError(
                        "Coordinate is required for left_click_drag action"
                    )
                action_builder.pointer_action.click_and_hold()
                action_builder.pointer_action.move_by(
                    action.coordinate.x, action.coordinate.y
                )
                action_builder.pointer_action.release()
                action_builder.perform()

            case "right_click":
                action_builder.pointer_action.context_click()
                action_builder.perform()

            case "middle_click":
                print("Middle mouse click not supported")

            case "double_click":
                action_builder.pointer_action.double_click()
                action_builder.perform()

            case "screenshot" | "cursor_position":
                # These are handled automatically
                pass

            case "scroll_down":
                action_builder.wheel_action.scroll(0, 0, 0, int(3* last_state.height / 4))
                action_builder.perform()

            case "scroll_up":
                action_builder.wheel_action.scroll(0, 0, 0, int(3* -last_state.height / 4))
                action_builder.perform()

            case _:
                raise ValueError(f"Unsupported action: {action.action}")

    def step(self) -> None:
        """Execute a single step of browser automation."""
        current_state = self.get_state()
        next_action = self.get_action(current_state)

        match next_action.action:
            case "success":
                self._status = BrowserGoalState.SUCCESS
                return
            case "failure":
                self._status = BrowserGoalState.FAILED
                return
            case _:
                self._status = BrowserGoalState.RUNNING
                self.take_action(next_action, current_state)

        self.history.append(BrowserStep(state=current_state, action=next_action))

    def start(self) -> None:
        """Start the browser automation process."""
        # Initialize mouse inside viewport
        actions = ActionChains(self.driver)
        actions.move_by_offset(1, 1).perform()

        while (
            self._status in (BrowserGoalState.INITIAL, BrowserGoalState.RUNNING)
            and len(self.history) <= self.max_steps
        ):
            self.step()
            time.sleep(self.wait_after_step_ms / 1000)  # Convert to seconds

            if self.pause_after_each_action:
                pause_for_input()

    @property
    def status(self) -> BrowserGoalState:
        """Get the current status of the browser automation."""
        return self._status
