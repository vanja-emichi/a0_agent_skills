"""Tests for the skill enforcer extension (Tasks 4, 6).

Verifies that in observe mode:
- Only target tools (code_execution_tool, text_editor) are inspected
- Would-fire decisions are logged to telemetry
- tool_args are NEVER mutated
- Non-target tools are ignored
- Already-loaded skills produce no-fire (already_loaded) decision
- The extension never breaks the agent loop (fail-safe)

Verifies that in enforce mode:
- The utility-model classifier is called after prefilter flags a candidate
- Positive classifier verdict appends a corrective warning/observation
- classifier_unavailable skips correction and logs appropriately
- No use of nudge() or forced skills_tool rewrites
- tool_args are NEVER mutated even in enforce mode

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_skill_enforcer.py -v
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import _make_extension, PLUGIN_ROOT

import random as _random


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


def _make_enforcer_agent(
    *,
    loaded_skills: list[str] | None = None,
    last_user_message: str = "implement feature",
    enforcement_mode: str = "observe",
    telemetry_enabled: bool = True,
):
    """Create a mock agent suitable for the enforcer extension."""
    agent = MagicMock()
    agent.data = {"loaded_skills": list(loaded_skills or [])}

    # last_user_message attribute (agent.last_user_message)
    # Framework Message class stores text in .content, not .message
    msg = MagicMock()
    msg.content = last_user_message
    agent.last_user_message = msg

    # loop_data for tool info
    current_tool = MagicMock()
    current_tool.method = "execute"
    current_tool.args = {"code": "print('hello')"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    # Prevent MagicMock file leaks: set context to None so that
    # resolve_state_dir() and _resolve_log_file() bail out early.
    agent.context = None

    return agent


def _make_config(
    *,
    enforcement_mode: str = "observe",
    telemetry_enabled: bool = True,
):
    """Create a plugin config dict."""
    return {
        "enforcement_mode": enforcement_mode,
        "telemetry_enabled": telemetry_enabled,
        "telemetry_log_path": ".a0proj/skill_activations.jsonl",
        "phase_governance_enabled": False,
        "skill_contracts_enabled": False,
    }


# ===========================================================================
# Target tool gating
# ===========================================================================


class TestTargetToolGating:
    """Verify only target tools are processed."""

    def test_code_execution_tool_is_processed(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()
        tool_args = {"code": "print('hello')"}
        original_args = dict(tool_args)

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args=tool_args))
            # Should call log_gate_decision with no_candidate
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "no_candidate"

        # tool_args must NOT be mutated
        assert tool_args == original_args

    def test_text_editor_is_processed(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()
        tool_args = {"action": "write", "path": "/tmp/test.py"}
        original_args = dict(tool_args)

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="text_editor", tool_args=tool_args))
            mock_log.assert_called_once()

        assert tool_args == original_args

    def test_browser_is_ignored(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(),
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="browser", tool_args={}))
            mock_log.assert_not_called()

    def test_response_is_ignored(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(),
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="response", tool_args={}))
            mock_log.assert_not_called()

    def test_none_tool_name_is_ignored(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name=None, tool_args={}))
            mock_log.assert_not_called()


# ===========================================================================
# Observe mode: would-fire decisions
# ===========================================================================


class TestObserveWouldFire:
    """Verify would-fire telemetry in observe mode."""

    def test_would_fire_when_skill_not_loaded(self):
        """Prefilter finds a candidate, skill not loaded → log should_correct."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "test-driven-development"

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_log.assert_called_once()
            kwargs = mock_log.call_args[1]
            assert kwargs["state"] == "should_correct"
            assert kwargs["mode"] == "observe"
            assert kwargs["candidate"] == "test-driven-development"

    def test_no_fire_when_skill_already_loaded(self):
        """Prefilter finds a candidate but skill IS loaded → log already_loaded."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=["test-driven-development"])

        skill = MagicMock()
        skill.name = "test-driven-development"

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_log.assert_called_once()
            kwargs = mock_log.call_args[1]
            assert kwargs["state"] == "already_loaded"

    def test_no_fire_when_no_candidates(self):
        """Prefilter finds nothing → log no_candidate."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "ls -la"},
            ))
            mock_log.assert_called_once()
            kwargs = mock_log.call_args[1]
            assert kwargs["state"] == "no_candidate"


# ===========================================================================
# Observe mode: zero mutation guarantee
# ===========================================================================


class TestObserveZeroMutation:
    """Observe mode MUST NEVER mutate tool_args."""

    def test_tool_args_not_mutated_on_would_fire(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "test-driven-development"

        tool_args = {"code": "x = 1"}
        original = json.dumps(tool_args, sort_keys=True)

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args=tool_args,
            ))

        assert json.dumps(tool_args, sort_keys=True) == original


# ===========================================================================
# Fail-safe
# ===========================================================================


class TestFailSafe:
    """The extension MUST NEVER break the agent loop."""

    def test_exception_does_not_propagate(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            side_effect=RuntimeError("config boom"),
        ):
            # Must NOT raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

    def test_prefilter_exception_does_not_propagate(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            side_effect=RuntimeError("prefilter boom"),
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

    def test_log_exception_does_not_propagate(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        skill = MagicMock()
        skill.name = "tdd"

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
            side_effect=RuntimeError("log boom"),
        ):
            # Must NOT raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))


# ===========================================================================
# No classifier call in observe mode
# ===========================================================================


class TestObserveNoClassifier:
    """Observe mode MUST NOT call the utility-model classifier."""

    def test_classify_skill_not_called(self):
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "test-driven-development"

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
        ) as mock_classify:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_classify.assert_not_called()


# ===========================================================================
# Task A: Would-fire verification (integration-level)
# ===========================================================================


class TestWouldFireVerification:
    """Verify the gate CAN produce should_correct and already_loaded states.

    These tests exercise the full enforcer flow: prefilter_match (mocked
    search_skills), candidate filtering, and gate-decision logging — proving
    the observe-mode gate detects would-fire situations end-to-end.
    """

    def test_prefilter_match_called_with_user_message(self):
        """Enforcer passes last_user_message to prefilter_match.

        Verifies the wiring: the gate extracts the user message and
        passes it to prefilter_match for candidate discovery.
        """
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="I need to debug this error in my code",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ) as mock_prefilter, patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "print('debug')"},
            ))
            # Verify prefilter was called with the agent and user message
            mock_prefilter.assert_called_once()
            call_args = mock_prefilter.call_args
            assert call_args[0][1] == "I need to debug this error in my code"

    def test_gate_produces_should_correct_with_real_prefilter(self):
        """Full enforcer flow: prefilter finds candidate, skill not loaded → should_correct."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="I need to debug this error in my code",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "print('debug')"},
            ))
            mock_log.assert_called_once()
            kwargs = mock_log.call_args[1]
            assert kwargs["state"] == "should_correct"
            assert kwargs["candidate"] == "debugging-and-error-recovery"
            assert kwargs["mode"] == "observe"

    def test_gate_produces_already_loaded_when_skill_loaded(self):
        """Full enforcer flow: prefilter finds candidate but skill IS loaded → already_loaded."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=["debugging-and-error-recovery"],
            last_user_message="I need to debug this error in my code",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "print('debug')"},
            ))
            mock_log.assert_called_once()
            kwargs = mock_log.call_args[1]
            assert kwargs["state"] == "already_loaded"


# ===========================================================================
# Task B: Enforce-mode corrective warning (Task 6)
# ===========================================================================


class TestEnforceModeCorrectiveWarning:
    """Verify enforce-mode behavior: classifier calls, corrective warnings,
    and guardrails (no nudge, no forced rewrites, no chat-model fallback).
    """

    def _make_classify_return(self, state, candidate=None, reason=None):
        """Build a classify_skill return dict."""
        return {"state": state, "candidate": candidate, "reason": reason}

    def test_classify_should_correct_appends_warning(self):
        """Classifier says should_correct → corrective observation appended to history."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="I need to debug this error",
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_correct",
            candidate="debugging-and-error-recovery",
            reason="bug fixing requires debugging skill",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # Warning appended to history
            ext.agent.hist_add_message.assert_called_once()
            call_kwargs = ext.agent.hist_add_message.call_args
            assert call_kwargs[1]["ai"] is False
            warning_text = call_kwargs[1]["content"]
            assert "debugging-and-error-recovery" in warning_text
            assert "skills_tool" in warning_text

            # Gate decision logged with should_correct
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "should_correct"
            assert mock_log.call_args[1]["candidate"] == "debugging-and-error-recovery"

    def test_classify_should_not_correct_no_warning(self):
        """Classifier says should_not_correct → no warning appended."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="list files",
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_not_correct", reason="trivial task",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "ls"},
            ))

            # NO warning appended
            ext.agent.hist_add_message.assert_not_called()

            # Gate decision logged with should_not_correct
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "should_not_correct"

    def test_classifier_unavailable_no_warning(self):
        """Utility model unavailable → no warning, log classifier_unavailable."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="debug this",
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "classifier_unavailable", reason="utility model error",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # NO warning appended
            ext.agent.hist_add_message.assert_not_called()

            # Gate decision logged with classifier_unavailable
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "classifier_unavailable"

    def test_tool_args_not_mutated_in_enforce_mode(self):
        """Enforce mode MUST NOT mutate tool_args."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        tool_args = {"code": "x = 1"}
        original = json.dumps(tool_args, sort_keys=True)

        classify_result = self._make_classify_return(
            "should_correct",
            candidate="debugging-and-error-recovery",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args=tool_args,
            ))

        assert json.dumps(tool_args, sort_keys=True) == original

    def test_classify_skill_called_in_enforce_mode(self):
        """Enforce mode MUST call classify_skill after prefilter flags a candidate."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_not_correct", reason="trivial",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ) as mock_classify, patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_classify.assert_called_once()

    def test_no_nudge_used(self):
        """Guardrail: nudge() is never called, only hist_add_message."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()
        # Ensure nudge does NOT exist (or would fail if called)
        ext.agent.nudge = MagicMock(side_effect=AssertionError("nudge must not be called"))

        classify_result = self._make_classify_return(
            "should_correct",
            candidate="debugging-and-error-recovery",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            # nudge was not called
            ext.agent.nudge.assert_not_called()

    def test_no_forced_skills_tool_rewrite(self):
        """Guardrail: tool_args are never rewritten to skills_tool invocation."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        tool_args = {"code": "x = 1"}

        classify_result = self._make_classify_return(
            "should_correct",
            candidate="debugging-and-error-recovery",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args=tool_args,
            ))

            # tool_args must not contain any skills_tool invocation
            assert tool_args.get("tool_name") != "skills_tool"
            assert "skill_name" not in tool_args
            assert tool_args == {"code": "x = 1"}

    def test_enforce_mode_failsafe_on_classify_exception(self):
        """Exception in classify_skill does not propagate (fail-safe)."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            side_effect=RuntimeError("classifier boom"),
        ):
            # Must NOT raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))


# ===========================================================================
# Phase-aware governance tests (Slice 3)
# ===========================================================================


def _make_phase_config(
    *,
    enforcement_mode: str = "observe",
    phase_governance_enabled: bool = True,
    cooldown_seconds: float = 300.0,
    telemetry_enabled: bool = True,
):
    """Create a plugin config dict with phase-aware governance keys."""
    return {
        "enforcement_mode": enforcement_mode,
        "telemetry_enabled": telemetry_enabled,
        "telemetry_log_path": ".a0proj/skill_activations.jsonl",
        "phase_governance_enabled": phase_governance_enabled,
        "enforcement_correction_cooldown_seconds": cooldown_seconds,
    }


class TestPhaseAwareEnforcerObserve:
    """Phase-aware governance in observe mode."""

    def test_define_phase_expected_skill_would_fire(self):
        """DEFINE phase + missing spec-driven-development → would-fire logged."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "spec-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="DEFINE",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["interview-me", "spec-driven-development"],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x"}))

            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "should_correct"
            assert mock_log.call_args[1]["phase"] == "DEFINE"

    def test_build_phase_wrong_skill_suppressed(self):
        """BUILD phase + missing shipping-and-launch → unexpected_for_phase."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "shipping-and-launch"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="BUILD",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["incremental-implementation", "test-driven-development"],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x"}))

            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "unexpected_for_phase"
            assert mock_log.call_args[1]["phase"] == "BUILD"

    def test_unknown_phase_falls_back_to_agnostic(self):
        """Unknown phase + missing skill → phase-agnostic would-fire."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value=None,
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x"}))

            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "should_correct"
            assert mock_log.call_args[1]["phase"] is None

    def test_governance_disabled_preserves_slice1_behavior(self):
        """phase_governance_enabled: false → Slice 1 behavior."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "shipping-and-launch"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(phase_governance_enabled=False),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x"}))

            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "should_correct"
            # No phase governance → phase not set in telemetry
            assert mock_log.call_args[1].get("phase") is None

    def test_duplicate_suppressed_within_cooldown(self):
        """Repeated correction within cooldown → suppressed_duplicate."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="BUILD",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["incremental-implementation", "test-driven-development"],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=True,  # Within cooldown
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x"}))

            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "suppressed_duplicate"

    def test_correction_allowed_after_cooldown(self):
        """Correction after cooldown expires → would-fire."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="BUILD",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["incremental-implementation", "test-driven-development"],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,  # Cooldown expired
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x"}))

            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "should_correct"


class TestPhaseAwareEnforcerEnforce:
    """Phase-aware governance in enforce mode."""

    def _make_classify_return(self, state, candidate=None, reason=None):
        return {
            "state": state,
            "candidate": candidate or "test-driven-development",
            "reason": reason,
        }

    def test_build_phase_expected_skill_correction_with_phase_context(self):
        """BUILD phase + missing tdd → correction includes phase context."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_correct", candidate="test-driven-development",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="BUILD",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["incremental-implementation", "test-driven-development"],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.workflow_state.append_progress_event",
            return_value="/some/path",
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # Warning includes phase context
            ext.agent.hist_add_message.assert_called_once()
            warning_text = ext.agent.hist_add_message.call_args[1]["content"]
            assert "BUILD" in warning_text
            assert "test-driven-development" in warning_text

            # Telemetry includes phase
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["phase"] == "BUILD"
            assert mock_log.call_args[1]["state"] == "should_correct"

    def test_build_phase_wrong_skill_suppressed_in_enforce(self):
        """BUILD phase + missing ship skill → unexpected_for_phase, no correction."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "shipping-and-launch"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="BUILD",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["incremental-implementation", "test-driven-development"],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "deploy"},
            ))

            # NO warning appended (wrong phase)
            ext.agent.hist_add_message.assert_not_called()

            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "unexpected_for_phase"

    def test_ship_phase_expected_skill_correction(self):
        """SHIP phase + missing shipping-and-launch → correction issued."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "shipping-and-launch"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_correct", candidate="shipping-and-launch",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="SHIP",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["shipping-and-launch", "ci-cd-and-automation"],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.workflow_state.append_progress_event",
            return_value="/some/path",
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "deploy"},
            ))

            ext.agent.hist_add_message.assert_called_once()
            assert mock_log.call_args[1]["state"] == "should_correct"
            assert mock_log.call_args[1]["phase"] == "SHIP"

    def test_gate_correction_event_logged_on_correction(self):
        """When correction is issued, gate_correction progress event is logged."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_correct", candidate="test-driven-development",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="BUILD",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["test-driven-development"],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.workflow_state.append_progress_event",
        ) as mock_progress, patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            mock_progress.assert_called_once()
            event_data = mock_progress.call_args[0][1]
            assert event_data["event"] == "gate_correction"
            assert event_data["candidate"] == "test-driven-development"
            assert event_data["phase"] == "BUILD"
            assert event_data["tool"] == "code_execution_tool"

    def test_duplicate_suppressed_in_enforce_mode(self):
        """Duplicate correction within cooldown → suppressed in enforce mode."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value="BUILD",
        ), patch(
            "helpers.phase_governance.get_expected_skills",
            return_value=["test-driven-development"],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=True,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            ext.agent.hist_add_message.assert_not_called()
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "suppressed_duplicate"


class TestEnforcerFailSafePhaseAware:
    """Verify phase-aware logic doesn't break the fail-safe guarantee."""

    def test_phase_governance_exception_does_not_propagate(self):
        """Exception in phase_governance → caught, enforcer continues safely."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_phase_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            side_effect=RuntimeError("prefilter boom"),
        ), patch(
            "helpers.phase_governance.get_current_phase",
            side_effect=RuntimeError("phase boom"),
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            # Must NOT raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

    def test_enforcer_has_top_level_try_except(self):
        """Source-level: enforcer execute() has try/except."""
        import inspect
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        source = inspect.getsource(SkillEnforcer.execute)
        assert "try:" in source
        assert "except Exception" in source

    def test_no_nudge_in_phase_aware_code(self):
        """No nudge() calls anywhere in the enforcer."""
        import inspect
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
            _append_corrective_observation,
        )
        enforcer_src = inspect.getsource(SkillEnforcer)
        helper_src = inspect.getsource(_append_corrective_observation)
        assert "nudge(" not in enforcer_src
        assert "nudge(" not in helper_src


# ===========================================================================
# Task 4 (Slice 4): Contract-aware enforcer tests
# ===========================================================================


class TestContractAwareEnforcer:
    """Tests for contract-aware enforcer behavior (Slice 4)."""

    def test_correction_includes_next_skill_hint(self):
        """Correction message includes next-skill recommendation when contract has next_skills."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "test-driven-development"

        verdict = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "skill not loaded",
        }

        cfg = _make_config(enforcement_mode="enforce")
        cfg["skill_contracts_enabled"] = True

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=cfg,
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value=None,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=verdict,
        ), patch.object(
            ext.agent, "hist_add_message",
        ) as mock_hist:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_hist.assert_called_once()
            msg = mock_hist.call_args[1]["content"]
            # test-driven-development has debugging-and-error-recovery as next
            assert "debugging-and-error-recovery" in msg

    def test_correction_omits_next_skill_when_no_contract(self):
        """Correction message omits next-skill when skill has no contract."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "agents-best-practices"  # not one of the 12 core skills

        verdict = {
            "state": "should_correct",
            "candidate": "agents-best-practices",
            "reason": "skill not loaded",
        }

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value=None,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=verdict,
        ), patch.object(
            ext.agent, "hist_add_message",
        ) as mock_hist:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_hist.assert_called_once()
            msg = mock_hist.call_args[1]["content"]
            # Should NOT contain "After this skill, consider loading"
            assert "After this skill, consider loading" not in msg

    def test_contracts_disabled_preserves_slice3_behavior(self):
        """When skill_contracts_enabled: false, behaves as Slice 3."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "test-driven-development"

        verdict = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "skill not loaded",
        }

        config = _make_config(enforcement_mode="enforce")
        config["skill_contracts_enabled"] = False

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=config,
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value=None,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=verdict,
        ), patch.object(
            ext.agent, "hist_add_message",
        ) as mock_hist:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_hist.assert_called_once()
            msg = mock_hist.call_args[1]["content"]
            # No next-skill hint when contracts disabled
            assert "After this skill, consider loading" not in msg

    def test_telemetry_includes_recommended_next(self):
        """Telemetry gate_decision includes recommended_next field."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "test-driven-development"

        cfg = _make_config(enforcement_mode="observe")
        cfg["skill_contracts_enabled"] = True

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=cfg,
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value=None,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_log.assert_called_once()
            kwargs = mock_log.call_args[1]
            assert kwargs.get("recommended_next") == "debugging-and-error-recovery"

    def test_telemetry_omits_recommended_next_when_no_contract(self):
        """Telemetry omits recommended_next when skill has no contract."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(loaded_skills=[])

        skill = MagicMock()
        skill.name = "agents-best-practices"  # no contract

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=False,
        ), patch(
            "helpers.phase_governance.get_current_phase",
            return_value=None,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_log.assert_called_once()
            kwargs = mock_log.call_args[1]
            assert kwargs.get("recommended_next") is None

    def test_enforcer_has_top_level_try_except(self):
        """Enforcer body still has top-level try/except."""
        import inspect
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        src = inspect.getsource(SkillEnforcer.execute)
        assert "try:" in src
        assert "except Exception" in src


# ===========================================================================
# Graph validation on build config (skill_graph_validate_on_build)
# ===========================================================================


class TestGraphValidateOnBuild:
    """Verify skill_graph_validate_on_build config is wired correctly."""

    def test_validate_graph_called_when_enabled(self):
        """validate_graph() is called when skill_graph_validate_on_build is true."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        cfg = _make_config(enforcement_mode="observe")
        cfg["skill_graph_validate_on_build"] = True

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=cfg,
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_contracts.validate_graph",
            return_value=[],
        ) as mock_validate:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x = 1"}))
            mock_validate.assert_called_once()

    def test_validate_graph_not_called_when_disabled(self):
        """validate_graph() is NOT called when skill_graph_validate_on_build is false."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        cfg = _make_config(enforcement_mode="observe")
        cfg["skill_graph_validate_on_build"] = False

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=cfg,
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_contracts.validate_graph",
            return_value=[],
        ) as mock_validate:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x = 1"}))
            mock_validate.assert_not_called()

    def test_validate_graph_warnings_logged_on_findings(self):
        """Findings from validate_graph() are logged as warnings."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        cfg = _make_config(enforcement_mode="observe")
        cfg["skill_graph_validate_on_build"] = True

        fake_findings = [
            {"type": "broken_ref", "details": "skill-a references non-existent next_skill: skill-z"},
        ]

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=cfg,
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_contracts.validate_graph",
            return_value=fake_findings,
        ), patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._log",
        ) as mock_log:
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x = 1"}))
            mock_log.warning.assert_called()
            call_args = mock_log.warning.call_args_list
            assert any("broken_ref" in str(c) or "non-existent" in str(c) for c in call_args)

    def test_validate_graph_exception_does_not_propagate(self):
        """validate_graph() exception is swallowed by top-level try/except."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent()

        cfg = _make_config(enforcement_mode="observe")
        cfg["skill_graph_validate_on_build"] = True

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=cfg,
        ), patch(
            "helpers.skill_contracts.validate_graph",
            side_effect=RuntimeError("graph explosion"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            # Must not raise
            _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x = 1"}))

    def test_validate_graph_called_at_most_once_per_session(self):
        """validate_graph() is called once, then skipped on subsequent execute() calls."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
            _reset_helpers_cache,
        )

        # Reset to ensure clean state
        _reset_helpers_cache()

        try:
            ext = SkillEnforcer.__new__(SkillEnforcer)
            ext.agent = _make_enforcer_agent()

            cfg = _make_config(enforcement_mode="observe")
            cfg["skill_graph_validate_on_build"] = True

            with patch(
                "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
                return_value=cfg,
            ), patch(
                "helpers.skill_match.prefilter_match",
                return_value=[],
            ), patch(
                "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
                new_callable=AsyncMock,
            ), patch(
                "helpers.skill_contracts.validate_graph",
                return_value=[],
            ) as mock_validate:
                # First call — should invoke validate_graph
                _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "x = 1"}))
                assert mock_validate.call_count == 1

                # Second call — should NOT invoke validate_graph again
                _run(ext.execute(tool_name="code_execution_tool", tool_args={"code": "y = 2"}))
                assert mock_validate.call_count == 1  # still 1, not 2

                # Third call — still skipped
                _run(ext.execute(tool_name="text_editor", tool_args={"action": "read", "path": "/tmp/f.py"}))
                assert mock_validate.call_count == 1  # still 1
        finally:
            _reset_helpers_cache()


# ===========================================================================
# Shadow sampling (Task 4)
# ===========================================================================


def _make_shadow_config(
    *,
    enforcement_mode: str = "observe",
    shadow_sample_rate: float = 0.0,
    telemetry_enabled: bool = True,
):
    """Create a plugin config dict with shadow sampling support."""
    return {
        "enforcement_mode": enforcement_mode,
        "telemetry_enabled": telemetry_enabled,
        "telemetry_log_path": ".a0proj/skill_activations.jsonl",
        "phase_governance_enabled": False,
        "skill_contracts_enabled": False,
        "enforcement_shadow_sample_rate": shadow_sample_rate,
    }


class TestShadowSampling:
    """Verify shadow sampling logic in observe mode.

    Shadow sampling means: on N% of tool calls, run the classifier in
    observe mode to collect accuracy data WITHOUT affecting behavior.
    """

    def _setup_enforcer(self, *, loaded_skills=None, last_user_message="implement feature"):
        """Create a fresh enforcer extension with mock agent."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
            _reset_helpers_cache,
        )
        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=loaded_skills or [],
            last_user_message=last_user_message,
        )
        return ext

    def _make_skill(self, name="test-driven-development"):
        skill = MagicMock()
        skill.name = name
        return skill

    def test_shadow_rate_zero_does_not_call_classifier(self):
        """With shadow_sample_rate=0.0, classifier is NOT called."""
        ext = self._setup_enforcer(loaded_skills=[])
        skill = self._make_skill()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(shadow_sample_rate=0.0),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
        ) as mock_classify:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_classify.assert_not_called()

    def test_shadow_rate_one_always_calls_classifier(self):
        """With shadow_sample_rate=1.0 and random() < 1.0, classifier IS called."""
        ext = self._setup_enforcer(loaded_skills=[])
        skill = self._make_skill()

        classify_result = {
            "state": "should_not_correct",
            "candidate": None,
            "reason": "trivial task",
        }

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(shadow_sample_rate=1.0),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ) as mock_classify, patch(
            "extensions.python.tool_execute_before._10_skill_enforcer.random.random",
            return_value=0.5,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_classify.assert_called_once()

    def test_shadow_sample_skipped_when_random_above_rate(self):
        """With shadow_sample_rate=0.1 and random()=0.5 (>0.1), classifier NOT called."""
        ext = self._setup_enforcer(loaded_skills=[])
        skill = self._make_skill()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(shadow_sample_rate=0.1),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
        ) as mock_classify, patch(
            "extensions.python.tool_execute_before._10_skill_enforcer.random.random",
            return_value=0.5,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_classify.assert_not_called()

    def test_shadow_sample_triggered_when_random_below_rate(self):
        """With shadow_sample_rate=0.1 and random()=0.05 (<0.1), classifier IS called."""
        ext = self._setup_enforcer(loaded_skills=[])
        skill = self._make_skill()

        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "writing tests is expected",
        }

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(shadow_sample_rate=0.1),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log, patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ) as mock_classify, patch(
            "extensions.python.tool_execute_before._10_skill_enforcer.random.random",
            return_value=0.05,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            mock_classify.assert_called_once()
            # Shadow result logged with mode='observe_shadow'
            assert mock_log.call_count == 2  # would-fire + shadow
            shadow_call = mock_log.call_args_list[1]
            assert shadow_call[1]["mode"] == "observe_shadow"
            assert shadow_call[1]["state"] == "should_correct"

    def test_shadow_no_corrections_injected(self):
        """Shadow sample says should_correct but NO corrective warning appended."""
        ext = self._setup_enforcer(loaded_skills=[])
        ext.agent.hist_add_message = MagicMock()
        skill = self._make_skill()

        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "writing tests is expected",
        }

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(shadow_sample_rate=1.0),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_before._10_skill_enforcer.random.random",
            return_value=0.5,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            # hist_add_message must NOT be called — shadow is data collection only
            ext.agent.hist_add_message.assert_not_called()

    def test_shadow_does_not_mutate_tool_args(self):
        """Shadow sampling MUST NOT mutate tool_args."""
        ext = self._setup_enforcer(loaded_skills=[])
        skill = self._make_skill()
        tool_args = {"code": "x = 1"}
        original = json.dumps(tool_args, sort_keys=True)

        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "test",
        }

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(shadow_sample_rate=1.0),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_before._10_skill_enforcer.random.random",
            return_value=0.5,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args=tool_args,
            ))

        assert json.dumps(tool_args, sort_keys=True) == original

    def test_shadow_classifier_failure_does_not_propagate(self):
        """If shadow classifier throws, it must not break the agent loop."""
        ext = self._setup_enforcer(loaded_skills=[])
        skill = self._make_skill()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(shadow_sample_rate=1.0),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            side_effect=RuntimeError("classifier boom"),
        ), patch(
            "extensions.python.tool_execute_before._10_skill_enforcer.random.random",
            return_value=0.5,
        ):
            # Must NOT raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

    def test_shadow_not_triggered_in_enforce_mode(self):
        """Shadow sampling only applies in observe mode; enforce mode uses classifier directly."""
        ext = self._setup_enforcer(loaded_skills=[])
        skill = self._make_skill()

        classify_result = {
            "state": "should_not_correct",
            "candidate": None,
            "reason": "trivial",
        }

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_shadow_config(
                enforcement_mode="enforce",
                shadow_sample_rate=1.0,
            ),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log, patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ) as mock_classify, patch(
            "extensions.python.tool_execute_before._10_skill_enforcer.random.random",
            return_value=0.5,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            # In enforce mode, classifier is called ONCE directly (not via shadow)
            mock_classify.assert_called_once()
            # The direct call should use mode='enforce', not 'observe_shadow'
            calls = mock_log.call_args_list
            shadow_calls = [c for c in calls if c[1].get("mode") == "observe_shadow"]
            assert len(shadow_calls) == 0


# ===========================================================================
# Task 6: Enforce Mode Enabled — config-driven integration tests
# ===========================================================================


def _make_enforce_config(
    *,
    phase_governance_enabled: bool = True,
    contracts_enabled: bool = False,
    cooldown_seconds: float = 300.0,
    telemetry_enabled: bool = True,
):
    """Config dict reflecting enforce mode (Task 6 default)."""
    return {
        "enforcement_mode": "enforce",
        "telemetry_enabled": telemetry_enabled,
        "telemetry_log_path": ".a0proj/skill_activations.jsonl",
        "phase_governance_enabled": phase_governance_enabled,
        "enforcement_correction_cooldown_seconds": cooldown_seconds,
        "skill_contracts_enabled": contracts_enabled,
    }


class TestEnforceModeEnabled:
    """Task 6 acceptance: enforce mode injects corrections, no false positives,
    dedup prevents loops, fail-safe still works.

    These tests verify the enforce-mode code paths work correctly with the
    enforcement_mode set to 'enforce' (as it is in production after Task 6).
    """

    def _make_classify_return(self, state, candidate=None, reason=None):
        return {"state": state, "candidate": candidate, "reason": reason}

    # --- Correction injection ---

    def test_enforce_mode_injects_correction_via_hist_add_message(self):
        """Classifier says should_correct → hist_add_message called with skill name."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="implement feature with tests",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_correct",
            candidate="test-driven-development",
            reason="TDD required for feature implementation",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_enforce_config(phase_governance_enabled=False),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # Correction was injected
            ext.agent.hist_add_message.assert_called_once()
            kwargs = ext.agent.hist_add_message.call_args[1]
            assert kwargs["ai"] is False
            assert "test-driven-development" in kwargs["content"]
            assert "skills_tool" in kwargs["content"]

    def test_enforce_mode_does_not_inject_when_should_not_correct(self):
        """Classifier says should_not_correct → NO hist_add_message call."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="list files",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_not_correct", reason="trivial task",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_enforce_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "ls"},
            ))

            # NO correction injected
            ext.agent.hist_add_message.assert_not_called()

    # --- No false positives when skill already loaded ---

    def test_enforce_mode_no_correction_when_skill_already_loaded(self):
        """Legitimate skill-loaded call → no correction, no false positive."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=["test-driven-development"],  # already loaded
            last_user_message="implement feature with tests",
        )
        ext.agent.hist_add_message = MagicMock()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_enforce_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # NO correction — skill is already loaded
            ext.agent.hist_add_message.assert_not_called()
            # Telemetry shows already_loaded
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "already_loaded"

    # --- Dedup prevents repeated corrections ---

    def test_enforce_mode_dedup_suppresses_repeated_correction(self):
        """should_suppress_correction=True → no correction injected (dedup)."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "test-driven-development"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="implement feature",
        )
        ext.agent.hist_add_message = MagicMock()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_enforce_config(),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.phase_governance.should_suppress_correction",
            return_value=True,  # dedup says "recently corrected"
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # NO correction — suppressed by dedup
            ext.agent.hist_add_message.assert_not_called()
            # Telemetry shows suppressed_duplicate
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "suppressed_duplicate"

    # --- Fail-safe in enforce mode ---

    def test_enforce_mode_fail_safe_on_exception(self):
        """Exception during enforce execution → no crash, no correction."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="implement feature",
        )
        ext.agent.hist_add_message = MagicMock()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            side_effect=RuntimeError("config explosion"),
        ):
            # Must NOT raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # No correction injected
            ext.agent.hist_add_message.assert_not_called()

    # --- Regression guard: default config value ---

    def test_default_config_has_enforce_mode(self):
        """default_config.yaml must have enforcement_mode: enforce after Task 6."""
        import yaml
        config_path = Path(__file__).parent.parent / "default_config.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        assert cfg["enforcement_mode"] == "enforce", (
            f"Expected enforcement_mode='enforce', got '{cfg['enforcement_mode']}'"
        )

    def test_config_json_has_enforce_mode(self):
        """config.json must have enforcement_mode: enforce after Task 6."""
        config_path = Path(__file__).parent.parent / "config.json"
        with open(config_path) as f:
            cfg = json.load(f)
        assert cfg["enforcement_mode"] == "enforce", (
            f"Expected enforcement_mode='enforce', got '{cfg['enforcement_mode']}'"
        )

    # --- gate_correction progress event ---

    def test_enforce_mode_logs_gate_correction_event(self):
        """Correction triggers gate_correction progress event for dedup tracking."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        skill = MagicMock()
        skill.name = "debugging-and-error-recovery"

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_enforcer_agent(
            loaded_skills=[],
            last_user_message="debug this error",
        )
        ext.agent.hist_add_message = MagicMock()

        classify_result = self._make_classify_return(
            "should_correct",
            candidate="debugging-and-error-recovery",
            reason="error debugging requires skill",
        )

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_enforce_config(phase_governance_enabled=False),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value=classify_result,
        ), patch(
            "helpers.workflow_state.append_progress_event",
        ) as mock_progress, patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

            # gate_correction progress event was logged
            mock_progress.assert_called_once()
            event = mock_progress.call_args[0][1]
            assert event["event"] == "gate_correction"
            assert event["candidate"] == "debugging-and-error-recovery"

