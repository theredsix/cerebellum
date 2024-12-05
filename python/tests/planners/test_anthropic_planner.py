import pytest
from unittest.mock import Mock, patch
from cerebellum import (
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


@patch("cerebellum.planners.anthropic.Anthropic")
def test_init_with_default_options(mock_anthropic):
    planner = AnthropicPlanner(AnthropicPlannerOptions())
    assert planner.screenshot_history == 1
    assert planner.mouse_jitter_reduction == 5
    assert planner.input_token_usage == 0
    assert planner.output_token_usage == 0
    assert planner.debug_image_path is None
    assert planner.debug is False


@patch("cerebellum.planners.anthropic.Anthropic")
def test_init_with_custom_options(mock_anthropic):
    mock_client = Mock()
    options = AnthropicPlannerOptions(
        screenshot_history=2,
        mouse_jitter_reduction=10,
        debug_image_path="/tmp/debug.png",
        client=mock_client,
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
    scaling = ScalingRatio(
        ratio_x=2.0,
        ratio_y=2.0,
        old_size=Coordinate(x=200, y=200),
        new_size=Coordinate(x=100, y=100),
    )

    browser_coords = Coordinate(x=200, y=200)
    result = planner.browser_to_llm_coordinates(browser_coords, scaling)

    assert result.x == 100  # 200/2
    assert result.y == 100  # 200/2


def test_llm_to_browser_coordinates(planner):
    scaling = ScalingRatio(
        ratio_x=2.0,
        ratio_y=2.0,
        old_size=Coordinate(x=200, y=200),
        new_size=Coordinate(x=100, y=100),
    )

    llm_coords = Coordinate(x=50, y=50)
    result = planner.llm_to_browser_coordinates(llm_coords, scaling)

    # Result should be clamped between 1 and old_size
    assert result.x == 100  # min(max(floor(50 * 2), 1), 200)
    assert result.y == 100  # min(max(floor(50 * 2), 1), 200)
