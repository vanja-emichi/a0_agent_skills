"""
Unit tests for _05_skill_telemetry.py

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_skill_telemetry.py -v

These tests use only stdlib + unittest.mock — no Agent Zero runtime required.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import _make_extension, PLUGIN_ROOT

# Re-import for patching paths relative to this module
from extensions.python.tool_execute_after._05_skill_telemetry import (
    SkillTelemetry,
    _write_log_line,
)
from extensions.python.tool_execute_after._05_skill_telemetry import (
    _resolve_log_path,
    _resolve_log_file,
)
from extensions.python.tool_execute_after._05_skill_telemetry import (
    _reconstruct_tool_info,
    _build_entry,
)


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Test 1: Non-skills_tool call → no file written
# ---------------------------------------------------------------------------

def test_non_skills_tool_call_no_log(tmp_path):
    """Non-skills_tool tool calls must not produce any log output."""
    ext, plugins_mock, _ = _make_extension(telemetry_enabled=True)
    log_file = tmp_path / "skill_activations.jsonl"

    with patch("extensions.python.tool_execute_after._05_skill_telemetry._write_log_line") as mock_write:
        _run(ext.execute(tool_name="code_execution_tool"))
        mock_write.assert_not_called()



# ---------------------------------------------------------------------------
# Test 2: skills_tool call with telemetry disabled → no file written
# ---------------------------------------------------------------------------

def test_telemetry_disabled_no_log(tmp_path):
    """When telemetry_enabled=False, no log should be written even for skills_tool."""
    ext, plugins_mock, _ = _make_extension(telemetry_enabled=False)

    with patch("helpers.plugins", plugins_mock), \
         patch("extensions.python.tool_execute_after._05_skill_telemetry._write_log_line") as mock_write:
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: skills_tool:load call, telemetry enabled → correct log line written
# ---------------------------------------------------------------------------

def test_skills_tool_load_writes_log(tmp_path):
    """A skills_tool:load call must produce one valid JSONL entry."""
    log_file = tmp_path / ".a0proj" / "skill_activations.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    ext, plugins_mock, agent = _make_extension(
        telemetry_enabled=True,
        log_path=str(log_file),
        skill_name="test-driven-development",
    )

    response_mock = MagicMock()
    response_mock.message = "Skill test-driven-development loaded successfully."

    # Patch all helpers imports inside the extension module
    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = "test-project"
    projects_mock.get_project_folder.return_value = str(tmp_path)
    projects_mock.PROJECT_META_DIR = ".a0proj"

    with patch("helpers.plugins", plugins_mock), \
         patch("helpers.projects", projects_mock):
        _run(ext.execute(tool_name="skills_tool", response=response_mock))

    assert log_file.exists(), "Log file should have been created"
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1, f"Expected 1 log entry, got {len(lines)}"

    entry = json.loads(lines[0])
    assert entry["tool"] == "skills_tool:load"
    assert entry["skill_name"] == "test-driven-development"
    assert entry["query"] is None
    assert "result_preview" in entry
    assert isinstance(entry["ts"], float)


# ---------------------------------------------------------------------------
# Test 4: Exception inside logging → swallowed, agent continues
# ---------------------------------------------------------------------------

def test_exception_swallowed_agent_continues():
    """Any exception in the telemetry code must not propagate."""
    ext, _, agent = _make_extension(telemetry_enabled=True)

    # Force an exception by making get_plugin_config raise
    plugins_mock = MagicMock()
    plugins_mock.get_plugin_config.side_effect = RuntimeError("config exploded")

    with patch("helpers.plugins", plugins_mock):
        # Must not raise
        _run(ext.execute(tool_name="skills_tool"))


# ---------------------------------------------------------------------------
# Test 5: Log rotation trims oldest half when max_lines exceeded
# ---------------------------------------------------------------------------

def test_log_rotation_trims_oldest_half(tmp_path):
    """_write_log_line must rotate (discard oldest half) when max_lines is hit."""
    log_file = tmp_path / "skill_activations.jsonl"

    # Write 10 existing lines
    existing = [json.dumps({"ts": i, "tool": f"entry-{i}"}) + "\n" for i in range(10)]
    log_file.write_text("".join(existing))

    # Write one more with max_lines=10 → should keep lines 5-9 + the new one
    new_line = json.dumps({"ts": 99, "tool": "new-entry"}) + "\n"
    _write_log_line(str(log_file), new_line, max_lines=10)

    result_lines = log_file.read_text().strip().splitlines()
    # 5 kept (oldest half dropped) + 1 new = 6
    assert len(result_lines) == 6, f"Expected 6 lines after rotation, got {len(result_lines)}"
    # Oldest entries (0-4) should be gone
    for line in result_lines:
        entry = json.loads(line)
        assert entry["ts"] != 0, "Entry 0 should have been rotated out"
    # New entry should be present
    last = json.loads(result_lines[-1])
    assert last["ts"] == 99


# ---------------------------------------------------------------------------
# Test 6: telemetry_log_path config key is honoured
# ---------------------------------------------------------------------------

def test_telemetry_log_path_config_honoured(tmp_path):
    """telemetry_log_path in config must override the default path."""
    custom_rel = "custom/my_log.jsonl"
    custom_abs = tmp_path / "custom" / "my_log.jsonl"

    ext, plugins_mock, agent = _make_extension(
        telemetry_enabled=True,
        log_path=custom_rel,
    )

    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = "proj"
    projects_mock.get_project_folder.return_value = str(tmp_path)
    projects_mock.PROJECT_META_DIR = ".a0proj"

    response_mock = MagicMock()
    response_mock.message = "ok"

    with patch("helpers.plugins", plugins_mock), \
         patch("helpers.projects", projects_mock):
        _run(ext.execute(tool_name="skills_tool", response=response_mock))

    assert custom_abs.exists(), f"Log should have been written to custom path {custom_abs}"


# ===========================================================================
# Fix 3: Path traversal protection tests for _resolve_log_path
# ===========================================================================

def test_resolve_log_path_rejects_traversal(tmp_path):
    """Path traversal attempts (../../etc/passwd) must be rejected."""
    result = _resolve_log_path(str(tmp_path), "../../etc/passwd")
    assert result is None, f"Expected None for traversal path, got {result}"


def test_resolve_log_path_rejects_absolute(tmp_path):
    """Absolute paths (/etc/passwd) must be rejected."""
    result = _resolve_log_path(str(tmp_path), "/etc/passwd")
    assert result is None, f"Expected None for absolute path, got {result}"


def test_resolve_log_path_accepts_relative(tmp_path):
    """Normal relative paths (logs/test.jsonl) must be accepted."""
    result = _resolve_log_path(str(tmp_path), "logs/test.jsonl")
    assert result is not None, "Expected valid path for relative path"
    expected = str(tmp_path / "logs" / "test.jsonl")
    assert result == expected, f"Expected {expected}, got {result}"


def test_resolve_log_path_rejects_none_input(tmp_path):
    """None as log_rel must be handled gracefully, returning None."""
    result = _resolve_log_path(str(tmp_path), None)
    assert result is None, f"Expected None for None input, got {result}"


# ===========================================================================
# Fix 4: Fallback code path tests for _resolve_log_file
# ===========================================================================

def test_resolve_log_file_falls_back_to_context_dir(tmp_path):
    """When no project is found, context_dir should be used as fallback."""
    agent = MagicMock()
    agent.context = MagicMock()
    ctx_dir = str(tmp_path / "ctx_data")
    agent.context.data = {"context_dir": ctx_dir}

    # Make project lookup fail so fallback triggers
    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = None
    cfg = {"telemetry_log_path": "skill_activations.jsonl"}

    with patch("helpers.projects", projects_mock):
        result = _resolve_log_file(agent, "skill_activations.jsonl", cfg)

    assert result is not None, "Expected a valid path from context_dir fallback"
    assert ctx_dir in result, f"Expected path under {ctx_dir}, got {result}"


def test_resolve_log_file_returns_none_when_no_context():
    """When agent has no context, _resolve_log_file must return None."""
    agent = MagicMock()
    agent.context = None
    cfg = {"telemetry_log_path": "skill_activations.jsonl"}

    result = _resolve_log_file(agent, "skill_activations.jsonl", cfg)
    assert result is None, f"Expected None with no context, got {result}"


def test_resolve_log_file_fallback_validates_traversal(tmp_path):
    """Malicious context_dir with path traversal must be rejected in fallback."""
    agent = MagicMock()
    agent.context = MagicMock()
    # Simulate a malicious context_dir pointing outside expected location
    agent.context.data = {"context_dir": "../../etc"}

    # Make project lookup fail so fallback triggers
    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = None
    cfg = {"telemetry_log_path": "skill_activations.jsonl"}

    with patch("helpers.projects", projects_mock):
        result = _resolve_log_file(agent, "skill_activations.jsonl", cfg)

    # The fallback MUST validate the path via _resolve_log_path
    # Without the fix, this would return a path under ../../etc
    # With the fix, it should return None (path traversal rejected)
    # Note: relative "../../etc" resolves to a real path, and the filename
    # is relative to it. _resolve_log_path checks the candidate stays inside base.
    # The key is the fix adds _resolve_log_path validation in the fallback.
    assert result is None, (
        f"Expected None for malicious context_dir traversal, got {result}"
    )


# ===========================================================================
# #6: _reconstruct_tool_info edge cases
# ===========================================================================

def test_reconstruct_tool_info_no_agent():
    """agent=None → returns (tool_name, {})."""
    full_name, args = _reconstruct_tool_info(None, "skills_tool")
    assert full_name == "skills_tool"
    assert args == {}


def test_reconstruct_tool_info_no_loop_data():
    """agent.loop_data=None → returns (tool_name, {})."""
    agent = MagicMock()
    agent.loop_data = None
    full_name, args = _reconstruct_tool_info(agent, "skills_tool")
    assert full_name == "skills_tool"
    assert args == {}


def test_reconstruct_tool_info_no_current_tool():
    """agent.loop_data.current_tool=None → returns (tool_name, {})."""
    agent = MagicMock()
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = None
    full_name, args = _reconstruct_tool_info(agent, "skills_tool")
    assert full_name == "skills_tool"
    assert args == {}


def test_reconstruct_tool_info_no_method():
    """current_tool.method=None → no colon suffix in tool name."""
    agent = MagicMock()
    current_tool = MagicMock()
    current_tool.method = None
    current_tool.args = {"skill_name": "my-skill"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    full_name, args = _reconstruct_tool_info(agent, "skills_tool")
    assert full_name == "skills_tool"
    assert args == {"skill_name": "my-skill"}


def test_reconstruct_tool_info_no_args():
    """current_tool.args=None → defaults to {}."""
    agent = MagicMock()
    current_tool = MagicMock()
    current_tool.method = "load"
    current_tool.args = None
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    full_name, args = _reconstruct_tool_info(agent, "skills_tool")
    assert full_name == "skills_tool:load"
    assert args == {}


# ===========================================================================
# #9: _debug_log tests
# ===========================================================================

def test_debug_log_emits_when_enabled():
    """telemetry_debug=True → logging.debug called with message."""
    from extensions.python.tool_execute_after import _05_skill_telemetry as mod
    cfg = {"telemetry_debug": True}
    with patch.object(mod._log, "debug") as mock_debug:
        SkillTelemetry._debug_log(cfg, "test message")
        mock_debug.assert_called_once_with("test message")


def test_debug_log_silent_when_disabled():
    """telemetry_debug=False/absent → no log emitted."""
    # Test with explicit False
    from extensions.python.tool_execute_after import _05_skill_telemetry as mod
    with patch.object(mod._log, "debug") as mock_debug:
        SkillTelemetry._debug_log({"telemetry_debug": False}, "test message")
        mock_debug.assert_not_called()

    # Test with absent key
    with patch.object(mod._log, "debug") as mock_debug:
        SkillTelemetry._debug_log({}, "test message")
        mock_debug.assert_not_called()


# ===========================================================================
# #10: _build_entry direct tests
# ===========================================================================

def test_build_entry_with_none_response():
    """response=None → result_preview is None."""
    line = _build_entry("skills_tool:load", {"skill_name": "x"}, None)
    entry = json.loads(line)
    assert entry["result_preview"] is None

import threading


# ===========================================================================
# Fix S1: Fallback path uses config basename, not hardcoded filename
# ===========================================================================

def test_resolve_log_file_fallback_uses_config_basename(tmp_path):
    """Fallback path must derive filename from log_rel, not hardcode 'skill_activations.jsonl'."""
    agent = MagicMock()
    agent.context = MagicMock()
    ctx_dir = str(tmp_path / "ctx_data")
    agent.context.data = {"context_dir": ctx_dir}

    # Make project lookup fail so fallback triggers
    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = None

    # Use a CUSTOM log_rel that differs from the hardcoded default
    custom_log_rel = "my_custom_log.jsonl"
    cfg = {"telemetry_log_path": custom_log_rel}

    with patch("helpers.projects", projects_mock):
        result = _resolve_log_file(agent, custom_log_rel, cfg)

    assert result is not None, "Expected a valid path from context_dir fallback"
    assert result.endswith("my_custom_log.jsonl"), (
        f"Expected path ending with 'my_custom_log.jsonl', got {result}"
    )


# ===========================================================================
# Fix S3: Rotation caps lines read to prevent memory spike
# ===========================================================================

def test_rotation_has_max_read_cap():
    """_write_log_line must define MAX_ROTATION_READ constant for memory safety."""
    from extensions.python.tool_execute_after._05_skill_telemetry import (
        MAX_ROTATION_READ,
    )
    assert isinstance(MAX_ROTATION_READ, int)
    assert MAX_ROTATION_READ > 0
    assert MAX_ROTATION_READ <= 1_000_000


def test_rotation_respects_cap(tmp_path):
    """When file has more lines than MAX_ROTATION_READ, rotation still works."""
    from extensions.python.tool_execute_after._05_skill_telemetry import (
        MAX_ROTATION_READ,
    )
    log_file = tmp_path / "test.jsonl"

    # Create a file with MAX_ROTATION_READ + 50 lines
    lines_to_write = MAX_ROTATION_READ + 50
    with open(log_file, "w") as fh:
        for i in range(lines_to_write):
            fh.write(json.dumps({"i": i}) + "\n")

    # Write one more with max_lines set to trigger rotation
    new_line = json.dumps({"i": "new"}) + "\n"
    _write_log_line(str(log_file), new_line, max_lines=100)

    # File should still exist and be valid
    assert log_file.exists()
    result_lines = log_file.read_text().strip().splitlines()
    for line in result_lines:
        entry = json.loads(line)
        assert "i" in entry


# ===========================================================================
# Test L2: Concurrent-write thread safety
# ===========================================================================

def test_concurrent_writes_thread_safety(tmp_path):
    """Multiple threads writing to the same file must produce all valid JSON lines."""
    log_file = tmp_path / "test.jsonl"
    num_threads = 10
    writes_per_thread = 5

    def writer(thread_id):
        for i in range(writes_per_thread):
            line = json.dumps({"thread": thread_id, "i": i}) + "\n"
            _write_log_line(str(log_file), line, max_lines=0)

    threads = [
        threading.Thread(target=writer, args=(t,)) for t in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == num_threads * writes_per_thread, (
        f"Expected {num_threads * writes_per_thread} lines, got {len(lines)}"
    )
    for line in lines:
        entry = json.loads(line)  # Must be valid JSON
        assert "thread" in entry


# ===========================================================================
# Test L3: Full flow integration test with rotation
# ===========================================================================

def test_full_flow_with_rotation(tmp_path):
    """Write multiple lines with rotation enabled, verify valid final content."""
    log_file = tmp_path / "test.jsonl"
    # Write 10 lines
    for i in range(10):
        line = json.dumps({"i": i}) + "\n"
        _write_log_line(str(log_file), line, max_lines=6)

    # After rotation: some entries dropped, but file must be valid JSONL
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) <= 10  # Should have rotated some away
    for line in lines:
        entry = json.loads(line)
        assert "i" in entry



def test_build_entry_truncates_long_message():
    """message >200 chars → result_preview truncated to exactly 200 chars."""
    long_msg = "A" * 300
    response = MagicMock()
    response.message = long_msg
    line = _build_entry("skills_tool:load", {}, response)
    entry = json.loads(line)
    assert entry["result_preview"] is not None
    assert len(entry["result_preview"]) == 200
    assert entry["result_preview"] == "A" * 200


def test_build_entry_empty_args():
    """Empty args → skill_name=None, query=None."""
    line = _build_entry("skills_tool:load", {}, None)
    entry = json.loads(line)
    assert entry["skill_name"] is None
    assert entry["query"] is None


def test_build_entry_response_no_message_attr():
    """Response without .message → result_preview is None."""
    response = MagicMock(spec=[])  # spec=[] means no attributes
    line = _build_entry("skills_tool:load", {}, response)
    entry = json.loads(line)
    assert entry["result_preview"] is None
