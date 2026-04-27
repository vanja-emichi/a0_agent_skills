# tests/test_strike_tracker_extraction.py
"""TDD tests for strike tracker error extraction from A0 @extensible data format."""
import asyncio
import hashlib
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# Add plugin to path
sys.path.insert(0, "/home/debian/agent-zero/development/usr/plugins/a0_agent_skills")

# Block agent.py import to prevent langchain.embeddings.base failure (deprecated in langchain 0.3.x)
# Chain: helpers.tool -> agent -> models -> langchain.embeddings.base (broken)
import types as _types
_am = _types.ModuleType("agent")
_am.Agent = type("Agent", (), {})
_am.LoopData = type("LoopData", (), {})
_am.LoopData.__module__ = "agent"
_am.Agent.__module__ = "agent"
sys.modules["agent"] = _am


def _make_tracker():
    """Create a LifecycleStrikeTracker with a mocked agent."""
    from extensions.python._functions.agent.Agent.handle_exception.end._55_lifecycle_strike_tracker import (
        LifecycleStrikeTracker,
    )
    mock_agent = MagicMock()
    mock_agent.context = MagicMock()
    mock_agent.context.data = {}
    tracker = LifecycleStrikeTracker(agent=mock_agent)
    return tracker


def test_extract_error_message_from_data_dict():
    """Verify error extraction works with A0 actual @extensible data format.

    A0 passes: kwargs = {"data": {"args": ..., "kwargs": ..., "result": ..., "exception": <exc>}}
    """
    tracker = _make_tracker()

    test_error = RuntimeError("test error message")
    kwargs_with_data = {
        "data": {
            "args": (),
            "kwargs": {},
            "result": None,
            "exception": test_error,
        }
    }

    from agent import LoopData
    loop_data = LoopData()
    result = tracker._extract_error_message(loop_data, **kwargs_with_data)
    assert result is not None, "Should extract error from data['exception']"
    assert "test error message" in result


def test_extract_returns_none_on_success():
    """No exception means no error message."""
    tracker = _make_tracker()

    kwargs_no_error = {
        "data": {
            "args": (),
            "kwargs": {},
            "result": "some result",
            "exception": None,
        }
    }

    from agent import LoopData
    loop_data = LoopData()
    result = tracker._extract_error_message(loop_data, **kwargs_no_error)
    assert result is None, "Should return None when no exception"


def test_extract_handles_missing_data_key():
    """Gracefully handle kwargs without data key."""
    tracker = _make_tracker()

    from agent import LoopData
    loop_data = LoopData()
    result = tracker._extract_error_message(loop_data)
    assert result is None, "Should return None when no data key"


def test_extract_handles_string_exception():
    """Handle string-based exception in data."""
    tracker = _make_tracker()

    kwargs_with_string = {
        "data": {
            "args": (),
            "kwargs": {},
            "result": None,
            "exception": "some error string",
        }
    }

    from agent import LoopData
    loop_data = LoopData()
    result = tracker._extract_error_message(loop_data, **kwargs_with_string)
    assert result is not None
    assert "some error string" in result
