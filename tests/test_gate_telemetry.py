"""Tests for gate decision telemetry (Task 3).

Verifies that gate decisions are logged to the same JSONL file as skill
activations, with proper entry shape, and that existing activation logging
remains unaffected.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_gate_telemetry.py -v
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import _make_extension, PLUGIN_ROOT


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    import asyncio
    return asyncio.run(coro)


# ===========================================================================
# _build_gate_entry
# ===========================================================================


class TestBuildGateEntry:
    """Verify gate decision entry format."""

    def test_entry_has_required_fields(self):
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            _build_gate_entry,
        )
        line = _build_gate_entry(
            tool_name="code_execution_tool",
            mode="observe",
            state="should_correct",
            candidate="test-driven-development",
            reason="writing tests without TDD skill",
        )
        entry = json.loads(line)
        assert "ts" in entry
        assert entry["event"] == "gate_decision"
        assert entry["tool"] == "code_execution_tool"
        assert entry["mode"] == "observe"
        assert entry["state"] == "should_correct"
        assert entry["candidate"] == "test-driven-development"
        assert entry["reason"] == "writing tests without TDD skill"

    def test_entry_with_none_optional_fields(self):
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            _build_gate_entry,
        )
        line = _build_gate_entry(
            tool_name="text_editor",
            mode="observe",
            state="no_candidate",
            candidate=None,
            reason=None,
        )
        entry = json.loads(line)
        assert entry["candidate"] is None
        assert entry["reason"] is None

    def test_entry_is_jsonl_line(self):
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            _build_gate_entry,
        )
        line = _build_gate_entry(
            tool_name="code_execution_tool",
            mode="enforce",
            state="classifier_unavailable",
            candidate=None,
            reason="utility model timeout",
        )
        assert line.endswith("\n")
        assert json.loads(line)  # valid JSON

    def test_entry_distinguishes_from_activation(self):
        """Gate entries have 'event' field; activation entries do not."""
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            _build_gate_entry,
            _build_entry,
        )
        gate_line = _build_gate_entry(
            "code_execution_tool", "observe", "should_correct", "tdd", "reason"
        )
        gate = json.loads(gate_line)
        assert gate["event"] == "gate_decision"

        # Activation entry does NOT have 'event' field
        activation_line = _build_entry("skills_tool:load", {"skill_name": "tdd"}, None)
        activation = json.loads(activation_line)
        assert "event" not in activation


# ===========================================================================
# log_gate_decision
# ===========================================================================


class TestLogGateDecision:
    """Verify gate decision logging writes to the correct file."""

    def test_writes_to_same_file_as_activations(self, tmp_path):
        """Both gate decisions and activations should go to the same JSONL."""
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            log_gate_decision,
        )
        log_file = tmp_path / "telemetry.jsonl"
        log_file.write_text("")  # create empty file

        agent = MagicMock()
        agent.context = MagicMock()
        cfg = {
            "telemetry_enabled": True,
            "telemetry_log_path": str(log_file),
        }

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._get_plugin_config",
            return_value=cfg,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
            return_value=str(log_file),
        ):
            _run(log_gate_decision(
                agent=agent,
                tool_name="code_execution_tool",
                mode="observe",
                state="should_correct",
                candidate="test-driven-development",
                reason="needs TDD",
            ))

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["event"] == "gate_decision"
        assert entry["state"] == "should_correct"

    def test_disabled_telemetry_skips_logging(self, tmp_path):
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            log_gate_decision,
        )
        log_file = tmp_path / "telemetry.jsonl"
        log_file.write_text("")

        agent = MagicMock()
        cfg = {"telemetry_enabled": False}

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._get_plugin_config",
            return_value=cfg,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
            return_value=str(log_file),
        ):
            _run(log_gate_decision(
                agent=agent,
                tool_name="code_execution_tool",
                mode="observe",
                state="should_correct",
                candidate="tdd",
                reason="test",
            ))

        content = log_file.read_text().strip()
        assert content == ""

    def test_no_log_path_skips_logging(self):
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            log_gate_decision,
        )
        agent = MagicMock()
        cfg = {"telemetry_enabled": True}

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._get_plugin_config",
            return_value=cfg,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
            return_value=None,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line",
        ) as mock_write:
            _run(log_gate_decision(
                agent=agent,
                tool_name="code_execution_tool",
                mode="observe",
                state="no_candidate",
                candidate=None,
                reason=None,
            ))
            mock_write.assert_not_called()

    def test_failure_does_not_raise(self, tmp_path):
        """Gate decision logging MUST NOT raise exceptions."""
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            log_gate_decision,
        )
        agent = MagicMock()
        # Config will fail to resolve, but should not raise
        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._get_plugin_config",
            side_effect=RuntimeError("boom"),
        ):
            # Should NOT raise
            _run(log_gate_decision(
                agent=agent,
                tool_name="code_execution_tool",
                mode="observe",
                state="should_correct",
                candidate="tdd",
                reason="test",
            ))

    def test_logs_classifier_unavailable(self, tmp_path):
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            log_gate_decision,
        )
        log_file = tmp_path / "telemetry.jsonl"
        log_file.write_text("")

        agent = MagicMock()
        cfg = {"telemetry_enabled": True}

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._get_plugin_config",
            return_value=cfg,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
            return_value=str(log_file),
        ):
            _run(log_gate_decision(
                agent=agent,
                tool_name="code_execution_tool",
                mode="enforce",
                state="classifier_unavailable",
                candidate=None,
                reason="utility model timeout",
            ))

        entry = json.loads(log_file.read_text().strip())
        assert entry["event"] == "gate_decision"
        assert entry["state"] == "classifier_unavailable"
        assert entry["mode"] == "enforce"
        assert entry["reason"] == "utility model timeout"

    def test_logs_observe_mode(self, tmp_path):
        from extensions.python.tool_execute_after._05_skill_telemetry import (
            log_gate_decision,
        )
        log_file = tmp_path / "telemetry.jsonl"
        log_file.write_text("")

        agent = MagicMock()
        cfg = {"telemetry_enabled": True}

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._get_plugin_config",
            return_value=cfg,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
            return_value=str(log_file),
        ):
            _run(log_gate_decision(
                agent=agent,
                tool_name="text_editor",
                mode="observe",
                state="already_loaded",
                candidate=None,
                reason=None,
            ))

        entry = json.loads(log_file.read_text().strip())
        assert entry["mode"] == "observe"
        assert entry["state"] == "already_loaded"


# ===========================================================================
# Existing activation logging preserved
# ===========================================================================


class TestActivationLoggingPreserved:
    """Existing skills_tool activation logging must still work."""

    def test_skills_tool_activation_still_logged(self, tmp_path):
        """Activation logging should not be affected by gate decision additions."""
        ext, plugins_mock, agent = _make_extension(telemetry_enabled=True)
        log_file = tmp_path / "telemetry.jsonl"
        log_file.write_text("")

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
            return_value=str(log_file),
        ):
            _run(ext.execute(
                tool_name="skills_tool",
                response=MagicMock(message="skill loaded"),
            ))

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) >= 1
        entry = json.loads(lines[0])
        # Activation entries don't have 'event' field
        assert "event" not in entry
        assert "skill_name" in entry or "tool" in entry
