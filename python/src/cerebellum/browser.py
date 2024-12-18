"""Browser automation components for Cerebellum (python).

This module provides the core browser automation functionality: state management,
action planning, and action execution.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union

from cerebellum.utils import parse_xdotool, pause_for_input
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.remote.webdriver import WebDriver


class BrowserGoalState(str, Enum):
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
class BrowserTab:
    """Information about one browser tab"""

    handle: str
    url: str
    title: str
    active: bool
    new: bool
    id: int


@dataclass
class BrowserState:
    """Comprehensive capture of browser state"""

    screenshot: str
    height: int
    width: int
    scrollbar: ScrollBar
    tabs: list[BrowserTab]
    active_tab: str
    active_element: Union[tuple[Coordinate, Coordinate], None]
    mouse: Coordinate


from enum import Enum


class BrowserActionType(str, Enum):
    """Enum of possible browser actions."""

    SUCCESS = "success"
    FAILURE = "failure"
    KEY = "key"
    TYPE = "type"
    MOUSE_MOVE = "mouse_move"
    LEFT_CLICK = "left_click"
    LEFT_CLICK_DRAG = "left_click_drag"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    DOUBLE_CLICK = "double_click"
    SCREENSHOT = "screenshot"
    CURSOR_POSITION = "cursor_position"
    SWITCH_TAB = "switch_tab"
    SCROLL_DOWN = "scroll_down"
    SCROLL_UP = "scroll_up"


@dataclass(frozen=True)
class BrowserAction:
    """An action to be performed on the browser."""

    action: BrowserActionType
    coordinate: Optional[Coordinate]
    text: Optional[str]
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

    additional_context: Optional[Union[str, dict[str, Any]]] = None
    additional_instructions: Optional[list[str]] = None
    wait_after_step_ms: Optional[int] = None
    pause_after_each_action: Optional[bool] = None
    max_steps: Optional[int] = None


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
        options: Optional[BrowserAgentOptions] = None,
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
        self.tabs: dict[str, BrowserTab] = {}

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

        mouse_position = self.get_mouse_position()
        scroll_position = self.get_scroll_position()

        tabs = self.driver.window_handles
        current_tab = self.driver.current_window_handle
        browser_tabs = []

        for tab in tabs:
            self.driver.switch_to.window(tab)
            tab_url = self.driver.current_url
            tab_title = self.driver.title
            is_active = tab == current_tab

            if tab in self.tabs:
                tab_id = self.tabs[tab].id
                is_new = False
            else:
                tab_id = len(self.tabs)
                is_new = True

            # Update / create tab information
            browser_tab = BrowserTab(
                handle=tab,
                url=tab_url,
                title=tab_title,
                active=is_active,
                new=is_new,
                id=tab_id,
            )

            self.tabs[tab] = browser_tab

            browser_tabs.append(browser_tab)

        # Switch back to the original active tab
        self.driver.switch_to.window(current_tab)

        # Get active element and its bounding box
        active_element: tuple[Coordinate, Coordinate] | None = None
        
        try:
            element = self.driver.switch_to.active_element
            if element and element.tag_name not in ["body", "iframe", "frame", "document"]:
                rect = self.driver.execute_script(
                    "return arguments[0].getBoundingClientRect();", 
                    element
                )
                print(rect)
                active_element = (
                    Coordinate(x=rect["x"],     y=rect["y"]),
                    Coordinate(x=rect["width"], y=rect["height"])
                )
        except:
            pass

        print(active_element)

        return BrowserState(
            screenshot=screenshot,
            height=viewport["y"],
            width=viewport["x"],
            scrollbar=scroll_position,
            tabs=browser_tabs,
            active_tab=current_tab,
            active_element=active_element,
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

        if action.action == BrowserActionType.KEY:
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

        elif action.action == BrowserActionType.TYPE:
            if not action.text:
                raise ValueError("Text is required for type action")
            action_builder.key_action.send_keys(action.text)
            action_builder.perform()

        elif action.action == BrowserActionType.MOUSE_MOVE:
            if not action.coordinate:
                raise ValueError("Coordinate is required for mouse_move action")
            action_builder.pointer_action.move_to_location(
                action.coordinate.x, action.coordinate.y
            )
            action_builder.perform()

        elif action.action == BrowserActionType.LEFT_CLICK:
            action_builder.pointer_action.click()
            action_builder.perform()

        elif action.action == BrowserActionType.LEFT_CLICK_DRAG:
            if not action.coordinate:
                raise ValueError("Coordinate is required for left_click_drag action")
            action_builder.pointer_action.click_and_hold()
            action_builder.pointer_action.move_by(
                action.coordinate.x, action.coordinate.y
            )
            action_builder.pointer_action.release()
            action_builder.perform()

        elif action.action == BrowserActionType.RIGHT_CLICK:
            action_builder.pointer_action.context_click()
            action_builder.perform()

        elif action.action == BrowserActionType.MIDDLE_CLICK:
            print("Middle mouse click not supported")

        elif action.action == BrowserActionType.DOUBLE_CLICK:
            action_builder.pointer_action.double_click()
            action_builder.perform()

        elif (
            action.action
            == BrowserActionType.SCREENSHOT | BrowserActionType.CURSOR_POSITION
        ):
            # These are handled automatically
            pass

        elif action.action == BrowserActionType.SCROLL_DOWN:
            action_builder.wheel_action.scroll(0, 0, 0, int(3 * last_state.height / 4))
            action_builder.perform()

        elif action.action == BrowserActionType.SCROLL_UP:
            action_builder.wheel_action.scroll(0, 0, 0, int(3 * -last_state.height / 4))
            action_builder.perform()

        elif action.action == BrowserActionType.SWITCH_TAB:
            if not action.text:
                raise ValueError("Text is required for switch_tab action")
            print(self.tabs)
            target_id = int(action.text)
            tab_handle = next(
                (handle for handle, tab in self.tabs.items() if tab.id == target_id),
                None,
            )
            print(action.text)
            print(tab_handle)
            if tab_handle is None:
                raise ValueError(f"No tab found with id: {action.text}")
            self.driver.switch_to.window(tab_handle)

        else:
            raise ValueError(f"Unsupported action: {action.action}")

    def step(self) -> None:
        """Execute a single step of browser automation."""
        current_state = self.get_state()
        next_action = self.get_action(current_state)

        if next_action.action == "success":
            self._status = BrowserGoalState.SUCCESS
            return
        elif next_action.action == "failure":
            self._status = BrowserGoalState.FAILED
            return
        else:
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
