"""Unit tests for SessionManager."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from core.session_manager import SessionManager, SessionState


@pytest.fixture
def mock_client():
    """Create a mock Gemini client."""
    client = Mock()
    client.aio = Mock()
    client.aio.live = Mock()
    return client


@pytest.mark.asyncio
async def test_session_initialization(mock_client):
    """Test session manager initialization."""
    session = SessionManager(
        client=mock_client,
        model="test-model",
        config={"test": "config"}
    )
    
    assert session.state == SessionState.DISCONNECTED
    assert not session.is_connected
    assert session.model == "test-model"


@pytest.mark.asyncio
async def test_session_state_transitions(mock_client):
    """Test session state transitions."""
    state_changes = []
    
    def track_state(state):
        state_changes.append(state)
    
    session = SessionManager(
        client=mock_client,
        model="test-model",
        on_state_change=track_state
    )
    
    # Simulate state changes
    session._set_state(SessionState.CONNECTING)
    session._set_state(SessionState.CONNECTED)
    session._set_state(SessionState.CLOSING)
    session._set_state(SessionState.CLOSED)
    
    assert state_changes == [
        SessionState.CONNECTING,
        SessionState.CONNECTED,
        SessionState.CLOSING,
        SessionState.CLOSED,
    ]


@pytest.mark.asyncio
async def test_conversation_history():
    """Test conversation history tracking."""
    mock_client = Mock()
    session = SessionManager(client=mock_client, model="test-model")
    
    # Manually add to history (simulating sends)
    session._conversation_history.append({
        "role": "user",
        "content": "Hello",
        "type": "text"
    })
    
    history = session.get_conversation_history()
    assert len(history) == 1
    assert history[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_session_reset():
    """Test session reset clears history."""
    mock_client = Mock()
    mock_client.aio.live.connect = AsyncMock()
    
    session = SessionManager(client=mock_client, model="test-model")
    
    # Add some history
    session._conversation_history.append({"test": "data"})
    assert len(session._conversation_history) == 1
    
    # Reset should clear history
    with patch.object(session, 'disconnect', new_callable=AsyncMock):
        with patch.object(session, 'connect', new_callable=AsyncMock):
            await session.reset()
    
    assert len(session._conversation_history) == 0
