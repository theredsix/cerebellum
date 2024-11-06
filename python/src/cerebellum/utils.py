import sys
import termios
import tty
from typing import NamedTuple

from selenium.webdriver.common.keys import Keys


def pause_for_input(prompt: str | None = None) -> bool:
    """Pause execution for keyboard input.

    This function temporarily changes terminal input to read every key, without
        requiring the user to hit enter. Can be used for examples such as captchas.
        Normal settings are restored afterwards.

    Example:
        >>> await pause_for_input()
        Press any key to continue...
        # Execution pauses until key press
    """
    # TODO: Verify win32 functionality, if not consider separate approach.
    # TODO: Have better return type for success bool
    print(prompt or "Press any key to continue...")

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return True


class KeyMapping(NamedTuple):
    """Class for keys and modifiers return."""

    modifiers: list[str]
    keys: list[str]


def parse_xdotool(xdotool_command: str) -> KeyMapping:
    """Parse an xdotool-style key command into Selenium key mappings.

    Args:
        xdotool_command: String containing the key command in xdotool format
            (e.g., "ctrl+c", "shift+alt+delete")

    Returns:
        KeyMapping containing lists of modifier and key constants for Selenium

    Example:
        >>> parse_xdotool("ctrl+c")
        KeyMapping(modifiers=[Keys.CONTROL], keys=['c'])
    """
    # Handle splitting and stripping leading/trailing whitespace
    key_parts = [part.strip().lower() for part in xdotool_command.split("+")]

    # Dictionary mapping xdotool keys to Selenium Keys constants
    key_mapping = {
        "ctrl": Keys.CONTROL,
        "alt": Keys.ALT,
        "shift": Keys.SHIFT,
        "super": Keys.META,
        "command": Keys.META,
        "meta": Keys.META,
        "null": Keys.NULL,
        "cancel": Keys.CANCEL,
        "help": Keys.HELP,
        "backspace": Keys.BACK_SPACE,
        "back_space": Keys.BACK_SPACE,
        "tab": Keys.TAB,
        "clear": Keys.CLEAR,
        "return": Keys.RETURN,
        "enter": Keys.RETURN,
        "pause": Keys.PAUSE,
        "escape": Keys.ESCAPE,
        "space": Keys.SPACE,
        "pageup": Keys.PAGE_UP,
        "page_up": Keys.PAGE_UP,
        "pagedown": Keys.PAGE_DOWN,
        "page_down": Keys.PAGE_DOWN,
        "end": Keys.END,
        "home": Keys.HOME,
        "left": Keys.ARROW_LEFT,
        "arrowleft": Keys.ARROW_LEFT,
        "arrow_left": Keys.ARROW_LEFT,
        "up": Keys.ARROW_UP,
        "arrowup": Keys.ARROW_UP,
        "arrow_up": Keys.ARROW_UP,
        "right": Keys.ARROW_RIGHT,
        "arrowright": Keys.ARROW_RIGHT,
        "arrow_right": Keys.ARROW_RIGHT,
        "down": Keys.ARROW_DOWN,
        "arrowdown": Keys.ARROW_DOWN,
        "arrow_down": Keys.ARROW_DOWN,
        "insert": Keys.INSERT,
        "delete": Keys.DELETE,
        "semicolon": Keys.SEMICOLON,
        "equals": Keys.EQUALS,
        "kp_0": Keys.NUMPAD0,
        "kp_1": Keys.NUMPAD1,
        "kp_2": Keys.NUMPAD2,
        "kp_3": Keys.NUMPAD3,
        "kp_4": Keys.NUMPAD4,
        "kp_5": Keys.NUMPAD5,
        "kp_6": Keys.NUMPAD6,
        "kp_7": Keys.NUMPAD7,
        "kp_8": Keys.NUMPAD8,
        "kp_9": Keys.NUMPAD9,
        "multiply": Keys.MULTIPLY,
        "add": Keys.ADD,
        "separator": Keys.SEPARATOR,
        "subtract": Keys.SUBTRACT,
        "decimal": Keys.DECIMAL,
        "divide": Keys.DIVIDE,
        "f1": Keys.F1,
        "f2": Keys.F2,
        "f3": Keys.F3,
        "f4": Keys.F4,
        "f5": Keys.F5,
        "f6": Keys.F6,
        "f7": Keys.F7,
        "f8": Keys.F8,
        "f9": Keys.F9,
        "f10": Keys.F10,
        "f11": Keys.F11,
        "f12": Keys.F12,
    }

    modifiers = [
        key_mapping.get(part.lower(), part)
        for part in key_parts
        if part.lower() in ["ctrl", "alt", "shift", "super", "command", "meta"]
    ]

    keys = [
        key_mapping.get(part.lower(), part)
        for part in key_parts
        if part.lower() not in ["ctrl", "alt", "shift", "super", "command", "meta"]
    ]

    return KeyMapping(modifiers=modifiers, keys=keys)
