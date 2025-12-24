"""Unit tests for ToolExecutor."""

import pytest
from tools.tool_executor import ToolExecutor
from google.genai import types


@pytest.fixture
def executor():
    """Create a tool executor instance."""
    return ToolExecutor(timeout=5.0)


@pytest.mark.asyncio
async def test_tool_registration(executor):
    """Test tool registration."""
    @executor.register_tool(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object"}
    )
    async def test_func(arg1: str):
        return f"Result: {arg1}"
    
    declarations = executor.get_tool_declarations()
    assert len(declarations) == 1
    assert len(declarations[0]["function_declarations"]) == 1
    assert declarations[0]["function_declarations"][0]["name"] == "test_tool"


@pytest.mark.asyncio
async def test_tool_execution(executor):
    """Test tool execution."""
    @executor.register_tool(
        name="add_numbers",
        description="Add two numbers",
    )
    async def add(a: int, b: int):
        return a + b
    
    # Create mock function call
    mock_call = Mock()
    mock_call.id = "test-id"
    mock_call.name = "add_numbers"
    mock_call.args = {"a": 5, "b": 3}
    
    result = await executor.execute_tool(mock_call)
    
    assert result.id == "test-id"
    assert result.name == "add_numbers"
    assert result.response["result"] == 8


@pytest.mark.asyncio
async def test_unknown_tool_error(executor):
    """Test error handling for unknown tools."""
    mock_call = Mock()
    mock_call.id = "test-id"
    mock_call.name = "unknown_tool"
    mock_call.args = {}
    
    result = await executor.execute_tool(mock_call)
    
    assert "error" in result.response
    assert "Unknown function" in result.response["error"]


@pytest.mark.asyncio
async def test_tool_timeout(executor):
    """Test tool execution timeout."""
    @executor.register_tool(
        name="slow_tool",
        description="A slow tool",
    )
    async def slow_func():
        import asyncio
        await asyncio.sleep(10)  # Longer than timeout
        return "done"
    
    mock_call = Mock()
    mock_call.id = "test-id"
    mock_call.name = "slow_tool"
    mock_call.args = {}
    
    result = await executor.execute_tool(mock_call)
    
    assert "error" in result.response
    assert "timed out" in result.response["error"]


from unittest.mock import Mock
