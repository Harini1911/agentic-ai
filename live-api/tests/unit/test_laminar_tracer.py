"""Unit tests for LaminarTracer."""

import pytest
from unittest.mock import Mock, patch
from observability.laminar_tracer import LaminarTracer


@pytest.fixture
def tracer():
    """Create a tracer instance with tracing disabled for testing."""
    return LaminarTracer(enabled=False)


def test_tracer_initialization():
    """Test tracer initialization."""
    tracer = LaminarTracer(enabled=False)
    assert not tracer.enabled
    assert tracer._session_id is None
    assert tracer._turn_count == 0


def test_set_session_id(tracer):
    """Test setting session ID."""
    tracer.set_session_id("test-session-123")
    assert tracer._session_id == "test-session-123"


def test_trace_session_context_manager(tracer):
    """Test session tracing context manager."""
    with tracer.trace_session("session-1", {"test": "metadata"}):
        assert tracer._session_id == "session-1"


def test_trace_turn_context_manager(tracer):
    """Test turn tracing context manager."""
    tracer.set_session_id("session-1")
    
    with tracer.trace_turn(1, "test input"):
        assert tracer._turn_count == 1
        assert tracer._turn_start_time is not None


def test_trace_tool_call_context_manager(tracer):
    """Test tool call tracing context manager."""
    with tracer.trace_tool_call("test_tool", {"arg": "value"}):
        pass  # Just verify no errors


def test_track_token_usage(tracer):
    """Test token usage tracking."""
    # Should not raise errors even when disabled
    tracer.track_token_usage(100, 50)


def test_track_error(tracer):
    """Test error tracking."""
    error = ValueError("Test error")
    tracer.track_error(error, "test context")


def test_track_state_change(tracer):
    """Test state change tracking."""
    tracer.track_state_change("CONNECTING", "CONNECTED")


def test_track_interruption(tracer):
    """Test interruption tracking."""
    tracer.track_interruption()
