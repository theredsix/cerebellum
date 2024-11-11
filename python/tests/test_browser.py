from unittest.mock import Mock
from cerebellum import (
    BrowserAgent,
    BrowserGoalState,
    BrowserAgentOptions,
    Coordinate,
)


def test_browser_agent_init():
    """Test BrowserAgent with no options."""
    driver = Mock()
    planner = Mock()
    agent = BrowserAgent(driver, planner, "Test goal")

    assert agent.goal == "Test goal"
    assert agent.additional_context == "None"
    assert agent.additional_instructions == []
    assert agent.wait_after_step_ms == 500
    assert agent.pause_after_each_action is False
    assert agent.max_steps == 50
    assert agent.status == BrowserGoalState.INITIAL
    assert agent.history == []


def test_browser_agent_with_options():
    """Test BrowserAgent initialization with options."""
    driver = Mock()
    planner = Mock()
    options = BrowserAgentOptions(
        additional_context="some context",
        additional_instructions=["instructions abc"],
        wait_after_step_ms=1234,
        pause_after_each_action=True,
        max_steps=567,
    )
    agent = BrowserAgent(driver, planner, "some goal", options)

    assert agent.additional_context == "some context"
    assert agent.additional_instructions == ["instructions abc"]
    assert agent.wait_after_step_ms == 1234
    assert agent.pause_after_each_action is True
    assert agent.max_steps == 567


def test_browser_agent_dict_context():
    """Test BrowserAgent with dictionary context."""
    driver = Mock()
    planner = Mock()
    options = BrowserAgentOptions(additional_context={"key": "value"})
    agent = BrowserAgent(driver, planner, "some goal", options)

    assert agent.additional_context == '{"key": "value"}'


def test_browser_goal_state_values():
    """Test BrowserGoalState string values match TypeScript implementation."""
    assert BrowserGoalState.INITIAL == "initial"
    assert BrowserGoalState.RUNNING == "running"
    assert BrowserGoalState.SUCCESS == "success"
    assert BrowserGoalState.FAILED == "failed"

    # Test string comparison works both ways
    assert "initial" == BrowserGoalState.INITIAL

    # Test type checking
    state = BrowserGoalState.INITIAL
    assert isinstance(state, BrowserGoalState)


def test_coordinate_class():
    """Test Coordinate class functionality."""
    coord = Coordinate(x=10, y=20)

    assert coord.x == 10
    assert coord.y == 20
