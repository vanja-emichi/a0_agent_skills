"""Guardrail regression tests for the skill enforcement gate (Task 7).

These tests are dedicated to asserting that forbidden primitives never
creep into the enforcer implementation.  They exist separately from the
behavioural tests in test_skill_enforcer.py so that a future developer
can run just the guardrail suite as a quick sanity check.

Guardrails asserted:
    1. nudge() is never called from the enforcer
    2. tool_args are never mutated in either mode
    3. No forced skills_tool rewrite in tool_args
    4. Enforce mode does not hard-pause (no InterventionException raised)
    5. Classifier unavailable degrades gracefully (no crash, no correction)
    6. No silent chat-model fallback (only utility model is used)
    7. Source-level: no nudge/import nudge in the enforcer module

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_enforcement_guardrails.py -v
"""

from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import PLUGIN_ROOT

ENFORCER_PATH = (
    PLUGIN_ROOT
    / "extensions"
    / "python"
    / "tool_execute_before"
    / "_10_skill_enforcer.py"
)


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


def _make_agent(
    *,
    loaded_skills: list[str] | None = None,
    last_user_message: str = "implement feature",
    enforcement_mode: str = "observe",
):
    """Create a mock agent suitable for guardrail tests."""
    agent = MagicMock()
    agent.data = {"loaded_skills": list(loaded_skills or [])}

    msg = MagicMock()
    msg.message = last_user_message
    agent.last_user_message = msg

    current_tool = MagicMock()
    current_tool.method = "execute"
    current_tool.args = {"code": "print('hello')"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    return agent


def _make_config(*, enforcement_mode: str = "observe"):
    """Create a plugin config dict."""
    return {
        "enforcement_mode": enforcement_mode,
        "telemetry_enabled": True,
        "telemetry_log_path": ".a0proj/skill_activations.jsonl",
    }


def _make_skill(name: str = "test-driven-development"):
    """Create a mock skill object."""
    skill = MagicMock()
    skill.name = name
    return skill


# ===========================================================================
# Guardrail 1: nudge() is never called
# ===========================================================================


class TestNudgeNeverCalled:
    """Assert that nudge() is never invoked by the enforcer in any mode."""

    def test_nudge_not_called_in_observe_mode(self):
        """Observe mode: nudge must never be called."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[])
        ext.agent.nudge = MagicMock(side_effect=AssertionError("nudge called!"))

        skill = _make_skill()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            ext.agent.nudge.assert_not_called()

    def test_nudge_not_called_in_enforce_mode_with_correction(self):
        """Enforce mode with should_correct: nudge must never be called."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()
        ext.agent.nudge = MagicMock(side_effect=AssertionError("nudge called!"))

        skill = _make_skill()
        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "tests needed",
        }

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
            ext.agent.nudge.assert_not_called()

    def test_nudge_not_called_in_enforce_mode_without_correction(self):
        """Enforce mode with should_not_correct: nudge must never be called."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()
        ext.agent.nudge = MagicMock(side_effect=AssertionError("nudge called!"))

        skill = _make_skill()
        classify_result = {
            "state": "should_not_correct",
            "candidate": None,
            "reason": "trivial",
        }

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
            ext.agent.nudge.assert_not_called()


class TestNoNudgeInSource:
    """Source-level check: the enforcer module must not import or reference nudge."""

    def test_source_does_not_contain_nudge(self):
        """The string 'nudge' must not appear in the enforcer source."""
        source = ENFORCER_PATH.read_text()
        # Allow only this test file and comments to mention nudge
        for line_no, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue
            assert "nudge" not in stripped.lower(), (
                f"Line {line_no} contains 'nudge': {line}"
            )


# ===========================================================================
# Guardrail 2: tool_args are never mutated in either mode
# ===========================================================================


class TestToolArgsNeverMutated:
    """Assert that tool_args dict is identical after enforcer runs."""

    def test_observe_mode_no_mutation(self):
        """Observe mode must not change tool_args."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[])

        skill = _make_skill()
        tool_args = {"code": "print('hello')"}
        original = json.dumps(tool_args, sort_keys=True)

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
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

    def test_enforce_mode_no_mutation_with_correction(self):
        """Enforce mode with should_correct must not change tool_args."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill()
        tool_args = {"code": "x = 1"}
        original = json.dumps(tool_args, sort_keys=True)

        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "needs tests",
        }

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

    def test_enforce_mode_no_mutation_text_editor(self):
        """Enforce mode on text_editor must not change tool_args."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill()
        tool_args = {"action": "write", "path": "/tmp/test.py", "content": "pass"}
        original = json.dumps(tool_args, sort_keys=True)

        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "needs tests",
        }

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
                tool_name="text_editor",
                tool_args=tool_args,
            ))

        assert json.dumps(tool_args, sort_keys=True) == original


# ===========================================================================
# Guardrail 3: No forced skills_tool rewrite
# ===========================================================================


class TestNoForcedSkillsToolRewrite:
    """Assert tool_args are never rewritten to contain skills_tool invocations."""

    def test_no_skills_tool_in_tool_args_observe(self):
        """Observe mode: tool_args must never contain skills_tool fields."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[])

        skill = _make_skill()
        tool_args = {"code": "x = 1"}

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="observe"),
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

        assert tool_args.get("tool_name") != "skills_tool"
        assert "skill_name" not in tool_args
        assert "action" not in tool_args or tool_args.get("action") == "x = 1"
        assert tool_args == {"code": "x = 1"}

    def test_no_skills_tool_in_tool_args_enforce(self):
        """Enforce mode: tool_args must never contain skills_tool fields."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill()
        tool_args = {"code": "x = 1"}

        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "needs tests",
        }

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

        assert tool_args.get("tool_name") != "skills_tool"
        assert "skill_name" not in tool_args
        assert tool_args == {"code": "x = 1"}


class TestNoSkillsToolRewriteInSource:
    """Source-level check: no tool_args mutation patterns in enforcer."""

    def test_source_does_not_assign_tool_name(self):
        """The enforcer source must not assign 'tool_name' to tool_args."""
        source = ENFORCER_PATH.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Subscript)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "tool_args"
                    ):
                        if isinstance(target.slice, ast.Constant):
                            assert target.slice.value != "tool_name", (
                                "Found tool_args['tool_name'] assignment in source"
                            )


# ===========================================================================
# Guardrail 4: No InterventionException / hard-pause
# ===========================================================================


class TestNoHardPause:
    """Assert enforce mode never raises InterventionException or similar."""

    def test_no_exception_raised_in_enforce_correct(self):
        """Enforce mode with correction must not raise any exception."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill()
        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "needs tests",
        }

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
            # Must not raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

    def test_no_intervention_exception_import(self):
        """Source must not import InterventionException."""
        source = ENFORCER_PATH.read_text()
        assert "InterventionException" not in source
        assert "intervention" not in source.lower() or source.lower().count("intervention") == 0

    def test_enforcer_return_type_is_none(self):
        """Execute method must return None (no intervention result)."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[])

        skill = _make_skill()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            return_value={
                "state": "should_correct",
                "candidate": "test-driven-development",
                "reason": "needs tests",
            },
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            ext.agent.hist_add_message = MagicMock()
            result = _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))
            # Return must be None — no intervention result
            assert result is None


# ===========================================================================
# Guardrail 5: Classifier unavailable degrades gracefully
# ===========================================================================


class TestClassifierUnavailableGracefulDegradation:
    """Assert classifier_unavailable state is handled safely."""

    def test_classifier_unavailable_no_crash(self):
        """Classifier unavailable must not crash the enforcer."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill()

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
            side_effect=RuntimeError("utility model unreachable"),
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ):
            # Must not raise
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args={"code": "x = 1"},
            ))

    def test_classifier_unavailable_no_warning_appended(self):
        """Classifier unavailable must not append any corrective warning."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill()
        classify_result = {
            "state": "classifier_unavailable",
            "candidate": None,
            "reason": "model error",
        }

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
            ext.agent.hist_add_message.assert_not_called()

    def test_classifier_unavailable_no_tool_args_mutation(self):
        """Classifier unavailable must not mutate tool_args."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill()
        tool_args = {"code": "x = 1"}
        original = json.dumps(tool_args, sort_keys=True)

        classify_result = {
            "state": "classifier_unavailable",
            "candidate": None,
            "reason": "model error",
        }

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


# ===========================================================================
# Guardrail 6: No silent chat-model fallback
# ===========================================================================


class TestNoChatModelFallback:
    """Assert the enforcer never falls back to the main chat model."""

    def test_no_call_llm_or_call_model_used(self):
        """Enforce mode must only use call_utility_model, never call_llm."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()
        # Trap: if call_llm is invoked, fail immediately
        ext.agent.call_llm = MagicMock(side_effect=AssertionError("call_llm must not be called"))
        ext.agent.call_model = MagicMock(side_effect=AssertionError("call_model must not be called"))

        skill = _make_skill()
        classify_result = {
            "state": "should_not_correct",
            "candidate": None,
            "reason": "trivial",
        }

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
            ext.agent.call_llm.assert_not_called()
            ext.agent.call_model.assert_not_called()

    def test_source_uses_only_utility_model(self):
        """Source-level: enforcer must not reference call_llm or call_model."""
        source = ENFORCER_PATH.read_text()
        # The enforcer delegates classification to skill_match.classify_skill
        # which uses agent.call_utility_model.  The enforcer itself should
        # never call the model directly.
        assert "call_llm" not in source
        assert ".call_model" not in source
        assert "call_utility_model" not in source or source.count("call_utility_model") == 0
        # classify_skill handles all model interaction


# ===========================================================================
# Guardrail 7: Already-loaded skill produces clean no-op
# ===========================================================================


class TestAlreadyLoadedNoOp:
    """Assert that when a skill is already loaded, the enforcer cleanly no-ops."""

    def test_already_loaded_no_correction_in_enforce(self):
        """Already-loaded skill: no correction, no warning, no mutation."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(
            loaded_skills=["debugging-and-error-recovery"],
            enforcement_mode="enforce",
        )
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill(name="debugging-and-error-recovery")
        tool_args = {"code": "x = 1"}
        original = json.dumps(tool_args, sort_keys=True)

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=_make_config(enforcement_mode="enforce"),
        ), patch(
            "helpers.skill_match.prefilter_match",
            return_value=[skill],
        ), patch(
            "helpers.skill_match.classify_skill",
            new_callable=AsyncMock,
        ) as mock_classify, patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args=tool_args,
            ))

            # Classifier must NOT be called when skill already loaded
            mock_classify.assert_not_called()
            # No warning appended
            ext.agent.hist_add_message.assert_not_called()
            # State should be already_loaded
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["state"] == "already_loaded"

        # No mutation
        assert json.dumps(tool_args, sort_keys=True) == original


# ===========================================================================
# Guardrail 8: Non-target-tool no-op
# ===========================================================================


class TestNonTargetToolNoOp:
    """Assert non-target tools are completely ignored."""

    @pytest.mark.parametrize("tool_name", [
        "browser",
        "response",
        "call_subordinate",
        "memory_save",
        "skills_tool",
        "search_engine",
    ])
    def test_non_target_tools_ignored(self, tool_name):
        """Non-target tools must produce no telemetry, no mutation."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[])

        tool_args = {"query": "test"}

        with patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name=tool_name,
                tool_args=tool_args,
            ))
            mock_log.assert_not_called()

        assert tool_args == {"query": "test"}


# ===========================================================================
# Guardrail 9: Corrective warning uses only hist_add_message
# ===========================================================================


class TestCorrectionMechanism:
    """Assert the correction mechanism is exclusively hist_add_message."""

    def test_correction_uses_hist_add_message_not_nudge(self):
        """Correction path must use hist_add_message, not nudge."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()
        ext.agent.nudge = MagicMock(side_effect=AssertionError("nudge!"))

        skill = _make_skill()
        classify_result = {
            "state": "should_correct",
            "candidate": "test-driven-development",
            "reason": "tests needed",
        }

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

            # hist_add_message was called (in-band warning)
            ext.agent.hist_add_message.assert_called_once()
            # nudge was NOT called
            ext.agent.nudge.assert_not_called()

    def test_warning_content_contains_skill_name_and_load_instruction(self):
        """Corrective warning must name the skill and instruct loading."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        ext.agent = _make_agent(loaded_skills=[], enforcement_mode="enforce")
        ext.agent.hist_add_message = MagicMock()

        skill = _make_skill(name="spec-driven-development")
        classify_result = {
            "state": "should_correct",
            "candidate": "spec-driven-development",
            "reason": "new feature needs spec",
        }

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

            call_kwargs = ext.agent.hist_add_message.call_args
            warning = call_kwargs[1]["content"]
            assert "spec-driven-development" in warning
            assert "skills_tool" in warning
            assert call_kwargs[1]["ai"] is False
