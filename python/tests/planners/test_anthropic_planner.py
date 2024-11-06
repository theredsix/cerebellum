import pytest
from unittest.mock import Mock, patch
from cerebellum.planners.anthropic import (
    AnthropicPlanner,
    AnthropicPlannerOptions,
    BrowserAction,
    BrowserState,
    Coordinate,
    ScrollBar,
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


def test_get_dimensions(planner):
    # Create a small test image and encode it
    from PIL import Image
    import io
    import base64

    img = Image.new("RGB", (100, 50), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_img = base64.b64encode(buf.getvalue()).decode()

    dimensions = planner.get_dimensions(b64_img)
    assert dimensions.x == 100
    assert dimensions.y == 50


def test_create_tool_use_id(planner):
    tool_id = planner.create_tool_use_id()
    assert tool_id.startswith("toolu_01")
    assert len(tool_id) == 30  # "toolu_01" + 22 random chars


def test_browser_to_llm_coordinates(planner):
    scaling = Mock(ratio=Coordinate(x=2, y=2), new_size=Coordinate(x=100, y=100))

    result = planner.browser_to_llm_coordinates(Coordinate(x=200, y=200), scaling)

    assert result.x == 100
    assert result.y == 100


def test_llm_to_browser_coordinates(planner):
    scaling = Mock(ratio=Coordinate(x=2, y=2), old_size=Coordinate(x=200, y=200))

    result = planner.llm_to_browser_coordinates(Coordinate(x=50, y=50), scaling)

    assert result.x == 100
    assert result.y == 100
