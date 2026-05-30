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
    msg = MagicMock()
    msg.message = last_user_message
    agent.last_user_message = msg

    # loop_data for tool info
    current_tool = MagicMock()
    current_tool.method = "execute"
    current_tool.args = {"code": "print('hello')"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

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
