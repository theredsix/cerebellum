import termios
from typing import Final

import pytest
from cerebellum import KeyMapping, parse_xdotool, pause_for_input
from selenium.webdriver.common.keys import Keys

# Constants for test values
CONTROL: Final = Keys.CONTROL
SHIFT: Final = Keys.SHIFT
ALT: Final = Keys.ALT
META: Final = Keys.META
RETURN: Final = Keys.RETURN
SPACE: Final = Keys.SPACE


def test_parse_xdotool_key_no_modifier() -> None:
    """Test parsing: one key no modifier."""
    assert parse_xdotool("a") == KeyMapping(modifiers=[], keys=["a"])
    assert parse_xdotool("return") == KeyMapping(modifiers=[], keys=[Keys.RETURN])


def test_parse_xdotool_modifier_no_key() -> None:
    """Test parsing: one modifier no key."""
    assert parse_xdotool("ctrl") == KeyMapping(modifiers=[Keys.CONTROL], keys=[])
    assert parse_xdotool("shift") == KeyMapping(modifiers=[Keys.SHIFT], keys=[])


def test_parse_xdotool_key_and_modifier() -> None:
    """Test parsing: one key one modifier."""
    assert parse_xdotool("ctrl+a") == KeyMapping(modifiers=[CONTROL], keys=["a"])
    assert parse_xdotool("shift+return") == KeyMapping(modifiers=[SHIFT], keys=[RETURN])


def test_parse_xdotool_multiple_keys_one_modifier() -> None:
    """Test parsing: multiple keys one modifier."""
    assert parse_xdotool("ctrl+a+b") == KeyMapping(modifiers=[CONTROL], keys=["a", "b"])
    assert parse_xdotool("shift+return+space") == KeyMapping(
        modifiers=[SHIFT], keys=[RETURN, SPACE]
    )


def test_parse_xdotool_one_key_multiple_modifiers() -> None:
    """Test parsing: one key multiple modifiers."""
    assert parse_xdotool("ctrl+shift+a") == KeyMapping(
        modifiers=[CONTROL, SHIFT], keys=["a"]
    )
    assert parse_xdotool("ctrl+alt+return") == KeyMapping(
        modifiers=[CONTROL, ALT], keys=[RETURN]
    )


def test_parse_xdotool_multiple_keys_multiple_modifiers() -> None:
    """Test parsing: multiple keys multiple modifiers."""
    assert parse_xdotool("ctrl+shift+a+b") == KeyMapping(
        modifiers=[CONTROL, SHIFT], keys=["a", "b"]
    )
    assert parse_xdotool("ctrl+alt+return+space") == KeyMapping(
        modifiers=[CONTROL, ALT], keys=[RETURN, SPACE]
    )


def test_parse_xdotool_empty() -> None:
    """Test parsing empty string."""
    assert parse_xdotool("") == KeyMapping(
        modifiers=[], keys=[""]  # Empty string key for empty input
    )


def test_parse_xdotool_equivalent_keys() -> None:
    """Test parsing that should return same keys."""
    # Test pageup variations
    assert parse_xdotool("pageup") == parse_xdotool("page_up")

    # Test return/enter variations
    assert parse_xdotool("return") == parse_xdotool("enter")

    # Test backspace
    assert parse_xdotool("backspace") == parse_xdotool("back_space")

    # Test arrow key variations
    assert parse_xdotool("left") == parse_xdotool("arrow_left")
    assert parse_xdotool("arrowleft") == parse_xdotool("arrow_left")

    assert parse_xdotool("up") == parse_xdotool("arrowup")
    assert parse_xdotool("arrowup") == parse_xdotool("arrow_up")

    assert parse_xdotool("down") == parse_xdotool("arrowdown")
    assert parse_xdotool("arrowdown") == parse_xdotool("arrow_down")

    assert parse_xdotool("right") == parse_xdotool("arrow_right")
    assert parse_xdotool("arrowright") == parse_xdotool("arrow_right")

    # Test meta
    assert parse_xdotool("super") == parse_xdotool("command")
    assert parse_xdotool("command") == parse_xdotool("meta")


def test_parse_xdotool_whitespace_handling() -> None:
    """Test whitespace handling in key commands.

    The current implementation preserves whitespace in the final keys array,
    matching the behavior of the TypeScript version.
    """
    # Leading/trailing whitespace is preserved in keys
    assert parse_xdotool("ctrl+a  ") == KeyMapping(modifiers=[CONTROL], keys=["a"])
    assert parse_xdotool("  ctrl+a") == KeyMapping(modifiers=[CONTROL], keys=["a"])

    # Internal whitespace behavior
    assert parse_xdotool("ctrl + a") == KeyMapping(modifiers=[CONTROL], keys=["a"])
    assert parse_xdotool("ctrl  +  a") == KeyMapping(modifiers=[CONTROL], keys=["a"])


def test_parse_xdotool_special_characters() -> None:
    """Test parsing of special characters and symbols.

    Verifies handling of special characters that might be used in keyboard shortcuts.
    """
    # Symbol keys
    assert parse_xdotool("shift+!") == KeyMapping(modifiers=[SHIFT], keys=["!"])
    assert parse_xdotool("ctrl+@") == KeyMapping(modifiers=[CONTROL], keys=["@"])
    assert parse_xdotool("alt+#") == KeyMapping(modifiers=[ALT], keys=["#"])

    # Punctuation
    assert parse_xdotool("ctrl+.") == KeyMapping(modifiers=[CONTROL], keys=["."])
    assert parse_xdotool("shift+,") == KeyMapping(modifiers=[SHIFT], keys=[","])


def test_parse_xdotool_complex_combinations() -> None:
    """Test complex key combinations with multiple modifiers and keys."""
    # Multiple modifiers
    assert parse_xdotool("ctrl+shift+alt+a") == KeyMapping(
        modifiers=[CONTROL, SHIFT, ALT], keys=["a"]
    )

    # Mixed case
    assert parse_xdotool("CTRL+Shift+Return") == KeyMapping(
        modifiers=[CONTROL, SHIFT], keys=[RETURN]
    )

    # All modifier combinations
    assert parse_xdotool("ctrl+alt+shift+meta+a") == KeyMapping(
        modifiers=[CONTROL, ALT, SHIFT, META], keys=["a"]
    )


def test_parse_xdotool_case_sensitivity() -> None:
    """Test case insensitivity in key and modifier parsing."""
    # Modifiers are case insensitive
    assert parse_xdotool("CTRL+a") == parse_xdotool("ctrl+a")
    assert parse_xdotool("Shift+a") == parse_xdotool("shift+a")
    assert parse_xdotool("ALT+a") == parse_xdotool("alt+a")

    # Special keys are case insensitive
    assert parse_xdotool("ctrl+RETURN") == parse_xdotool("ctrl+return")
    assert parse_xdotool("shift+SPACE") == parse_xdotool("shift+space")
    assert parse_xdotool("alt+PAGE_UP") == parse_xdotool("alt+pageup")


def test_parse_xdotool_unicode_characters() -> None:
    """Test handling of unicode characters in key commands."""
    # Basic unicode characters
    assert parse_xdotool("ctrl+é") == KeyMapping(modifiers=[CONTROL], keys=["é"])
    assert parse_xdotool("shift+ñ") == KeyMapping(modifiers=[SHIFT], keys=["ñ"])
    assert parse_xdotool("alt+ü") == KeyMapping(modifiers=[ALT], keys=["ü"])


def test_pause_for_input_basic(mock_terminal, capsys):
    """Test basic functionality of pause_for_input."""
    result = pause_for_input()

    # Check return value
    assert result is True

    # Verify terminal setup and cleanup
    mock_terminal["get_attr"].assert_called_once_with(0)
    mock_terminal["setraw"].assert_called_once_with(0)
    mock_terminal["set_attr"].assert_called_once_with(
        0, termios.TCSADRAIN, mock_terminal["get_attr"].return_value
    )

    # Check default prompt
    captured = capsys.readouterr()
    assert captured.out == "Press any key to continue...\n"


def test_pause_for_input_custom_prompt(mock_terminal, capsys):
    """Test pause_for_input with custom prompt."""
    custom_prompt = "Custom prompt message"
    pause_for_input(custom_prompt)

    captured = capsys.readouterr()
    assert captured.out == f"{custom_prompt}\n"


def test_pause_for_input_exception_handling(mock_terminal):
    """Test error handling during terminal operations."""
    mock_terminal["setraw"].side_effect = termios.error("Mock error")

    # Should still restore terminal settings even if an error occurs
    with pytest.raises(termios.error):
        pause_for_input()

    # Verify cleanup was attempted
    mock_terminal["set_attr"].assert_called_once_with(
        0, termios.TCSADRAIN, mock_terminal["get_attr"].return_value
    )


def test_pause_for_input_terminal_restoration(mock_terminal):
    """Test that terminal settings are properly restored."""
    original_settings = [1, 2, 3]
    mock_terminal["get_attr"].return_value = original_settings

    pause_for_input()

    # Verify original settings were restored
    mock_terminal["set_attr"].assert_called_once_with(
        0, termios.TCSADRAIN, original_settings
    )


def test_pause_for_input_input_reading(mock_terminal):
    """Test that input is properly read."""
    pause_for_input()

    # Verify input was read
    mock_terminal["stdin"].read.assert_called_once_with(1)


@pytest.mark.parametrize("key_input", ["a", "\n", " ", "\t"])
def test_pause_for_input_different_keys(mock_terminal, key_input):
    """Test pause_for_input with different key inputs."""
    mock_terminal["stdin"].read.return_value = key_input

    result = pause_for_input()

    assert result is True
    mock_terminal["stdin"].read.assert_called_once_with(1)
