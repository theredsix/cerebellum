import pytest
from unittest.mock import Mock, patch
from cerebellum.planners.anthropic import (
    AnthropicPlanner,
    AnthropicPlannerOptions,
    BrowserAction,
    BrowserState,
    Coordinate,
    ScrollBar,
    ScalingRatio,
)


@pytest.fixture
def mock_anthropic_client():
    return Mock()


@pytest.fixture
def planner(mock_anthropic_client):
    options = AnthropicPlannerOptions(client=mock_anthropic_client)
    return AnthropicPlanner(options)


def test_init_with_default_options():
    planner = AnthropicPlanner()
    assert planner.screenshot_history == 1
    assert planner.mouse_jitter_reduction == 5
    assert planner.input_token_usage == 0
    assert planner.output_token_usage == 0
    assert planner.debug_image_path is None
    assert planner.debug is False


def test_init_with_custom_options():
    options = AnthropicPlannerOptions(
        screenshot_history=2,
        mouse_jitter_reduction=10,
        debug_image_path="/tmp/debug.png",
    )
    planner = AnthropicPlanner(options)
    assert planner.screenshot_history == 2
    assert planner.mouse_jitter_reduction == 10
    assert planner.debug_image_path == "/tmp/debug.png"


def test_create_tool_use_id(planner):
    tool_id = planner.create_tool_use_id()
    assert tool_id.startswith("toolu_01")
    assert len(tool_id) == 30  # "toolu_01" + 22 random chars


def test_browser_to_llm_coordinates(planner):
    scaling = Mock()
    scaling.ratio_x = 2  # Set ratio_x to return 2
    scaling.ratio_y = 2  # Set ratio_y to return 2
    scaling.new_size = Coordinate(x=100, y=100)

    result = planner.browser_to_llm_coordinates(Coordinate(x=200, y=200), scaling)

    assert result.x == 100
    assert result.y == 100


def test_llm_to_browser_coordinates(planner):
    scaling = Mock()
    scaling.ratio_x = 2  # Set ratio_x to return 2
    scaling.ratio_y = 2  # Set ratio_y to return 2
    scaling.old_size = Coordinate(x=200, y=200)

    result = planner.llm_to_browser_coordinates(Coordinate(x=50, y=50), scaling)

    assert result.x == 100
    assert result.y == 100
