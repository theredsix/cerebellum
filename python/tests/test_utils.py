from selenium.webdriver.common.keys import Keys
from cerebellum.utils import parse_xdotool, KeyMapping


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
    assert parse_xdotool("ctrl+a") == KeyMapping(modifiers=[Keys.CONTROL], keys=["a"])

    assert parse_xdotool("shift+return") == KeyMapping(
        modifiers=[Keys.SHIFT], keys=[Keys.RETURN]
    )


def test_parse_xdotool_multiple_keys_one_modifier() -> None:
    """Test parsing: multiple keys one modifier."""
    assert parse_xdotool("ctrl+a+b") == KeyMapping(
        modifiers=[Keys.CONTROL], keys=["a", "b"]
    )

    assert parse_xdotool("shift+return+space") == KeyMapping(
        modifiers=[Keys.SHIFT], keys=[Keys.RETURN, Keys.SPACE]
    )


def test_parse_xdotool_one_key_multiple_modifiers() -> None:
    """Test parsing: one key multiple modifiers."""
    assert parse_xdotool("ctrl+shift+a") == KeyMapping(
        modifiers=[Keys.CONTROL, Keys.SHIFT], keys=["a"]
    )

    assert parse_xdotool("ctrl+alt+return") == KeyMapping(
        modifiers=[Keys.CONTROL, Keys.ALT], keys=[Keys.RETURN]
    )


def test_parse_xdotool_multiple_keys_multiple_modifiers() -> None:
    """Test parsing: multiple keys multiple modifiers."""
    assert parse_xdotool("ctrl+shift+a+b") == KeyMapping(
        modifiers=[Keys.CONTROL, Keys.SHIFT], keys=["a", "b"]
    )

    assert parse_xdotool("ctrl+alt+return+space") == KeyMapping(
        modifiers=[Keys.CONTROL, Keys.ALT], keys=[Keys.RETURN, Keys.SPACE]
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
