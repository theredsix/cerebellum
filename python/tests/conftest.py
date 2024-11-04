from typing import Any

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_terminal(mocker: MockerFixture) -> dict[str, Any]:
    """Mock terminal-related modules and functions.

    Args:
        mocker: PyTest mock fixture

    Returns:
        dict: Dictionary containing all mocked objects
    """
    # Mock termios module
    mock_termios = mocker.patch("termios")
    mock_termios.tcgetattr.return_value = [0] * 7  # Simulate terminal attributes
    mock_termios.TCSADRAIN = 1

    # Mock sys.stdin
    mock_stdin = mocker.patch("sys.stdin")
    mock_stdin.fileno.return_value = 0
    mock_stdin.read.return_value = "a"

    # Mock tty module
    mock_tty = mocker.patch("tty")

    return {"termios": mock_termios, "stdin": mock_stdin, "tty": mock_tty}
