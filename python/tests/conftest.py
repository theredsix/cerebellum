from unittest.mock import patch
import pytest


@pytest.fixture
def mock_terminal():
    """Fixture to mock terminal-related functions and modules."""
    with (
        patch("termios.tcgetattr") as mock_get_attr,
        patch("termios.tcsetattr") as mock_set_attr,
        patch("tty.setraw") as mock_setraw,
        patch("sys.stdin") as mock_stdin,
    ):

        # Setup mock return values
        mock_get_attr.return_value = [1, 2, 3]  # Mock terminal settings
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.return_value = "x"

        yield {
            "get_attr": mock_get_attr,
            "set_attr": mock_set_attr,
            "setraw": mock_setraw,
            "stdin": mock_stdin,
        }
