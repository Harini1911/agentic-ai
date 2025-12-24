"""Pytest configuration."""

import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)
