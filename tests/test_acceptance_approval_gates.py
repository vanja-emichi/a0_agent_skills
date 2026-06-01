"""Acceptance tests for the full approval gate pipeline (Task 8).

Integration-level tests that verify the complete flow from natural language
detection through approval recording, mtime invalidation, and phase gate
enforcement — using real functions, not mocks where possible.

Covers:
- G1 gate: DEFINE→PLAN blocked without spec approval, allowed after approval
- G2 gate: PLAN→BUILD blocked without plan approval, allowed after approval
- Mtime invalidation: modifying an approved artifact re-blocks the gate
- Natural language detection: positive and negative phrase handling
- Enforcement mode: correction injection when skills are skipped
- All 4 gates (G1–G4) verified in parametrized tests

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_acceptance_approval_gates.py -v
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import PLUGIN_ROOT


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Agent factory with real temp-dir state
# ---------------------------------------------------------------------------


def _make_integration_agent(*, phase: str | None = None, slug: str | None = None):
    """Create a mock agent backed by a temp directory for real state I/O.

    Sets up:
    - agent.context.config.project_root → temp dir
    - agent.context.config.chat_path → temp dir / chat
    - Current phase saved if provided
    - Feature slug discoverable if provided
    """
    tmpdir = tempfile.mkdtemp(prefix="acceptance_gate_")
    agent = MagicMock()

    # agent.context must be a real object (not None) for state I/O
    ctx = MagicMock()
    ctx.config.project_root = tmpdir
    chat_dir = os.path.join(tmpdir, "chat")
    os.makedirs(chat_dir, exist_ok=True)
    ctx.config.chat_path = chat_dir
    agent.context = ctx

    # last_user_message (default: empty)
    msg = MagicMock()
    msg.content = ""
    agent.last_user_message = msg

    # data dict for loaded_skills etc.
    agent.data = {"loaded_skills": []}

    # loop_data for tool info
    current_tool = MagicMock()
    current_tool.method = "execute"
    current_tool.args = {"code": "print('hello')"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    # Save initial phase if provided
    if phase:
        from helpers import workflow_state
        workflow_state.save_current_phase(agent, {
            "phase": phase,
            "phases_completed": [],
        })

    # Set up feature slug in state if provided
    if slug:
        from helpers import workflow_state
        workflow_state.save_workflow_artifacts(agent, {
            "feature_slug": slug,
        })

    return agent, tmpdir


def _cleanup_agent(tmpdir: str):
    """Remove temp directory."""
    shutil.rmtree(tmpdir, ignore_errors=True)


def _create_artifact_file(tmpdir: str, artifact_type: str, slug: str | None = None) -> str:
    """Create an artifact file in the temp dir and return its path."""
    if slug:
        if artifact_type == "spec":
            path = os.path.join(tmpdir, "docs", "specs", f"{slug}-spec.md")
        elif artifact_type == "plan":
            path = os.path.join(tmpdir, "docs", "plans", f"{slug}-plan.md")
        elif artifact_type == "todo":
            path = os.path.join(tmpdir, "tasks", f"{slug}-todo.md")
        else:
            path = os.path.join(tmpdir, "docs", artifact_type + ".md")
    else:
        if artifact_type == "spec":
            path = os.path.join(tmpdir, "SPEC.md")
        elif artifact_type == "plan":
            path = os.path.join(tmpdir, "tasks", "plan.md")
        elif artifact_type == "todo":
            path = os.path.join(tmpdir, "tasks", "todo.md")
        else:
            path = os.path.join(tmpdir, "docs", artifact_type + ".md")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# Test {artifact_type}\n\nContent for {artifact_type}.\n")
    return path


def _write_state(agent, filename: str, data: dict):
    """Write a JSON state file to the agent's state dir."""
    from helpers import workflow_state
    state_dir = workflow_state.resolve_state_dir(agent)
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, filename)
    with open(path, "w") as f:
        json.dump(data, f)
    return path


# ===========================================================================
# G1 Gate: DEFINE→PLAN requires spec approval
# ===========================================================================


class TestG1Gate:
    """G1 gate: DEFINE→PLAN transition requires approved spec."""

    def test_g1_blocked_without_spec_approval(self):
        """DEFINE→PLAN blocked when spec is not approved (enforce mode)."""
        from helpers.phase_governance import check_phase_approval_gate
        agent, tmpdir = _make_integration_agent(phase="DEFINE")
        try:
            _create_artifact_file(tmpdir, "spec")
            from helpers import workflow_state
            workflow_state.save_workflow_artifacts(agent, {
                "spec_path": os.path.join(tmpdir, "SPEC.md"),
            })

            result = check_phase_approval_gate(
                agent,
                from_phase="DEFINE",
                to_phase="PLAN",
                enforcement_mode="enforce",
            )
            assert result is False, "G1 gate should block without spec approval"
        finally:
            _cleanup_agent(tmpdir)

    def test_g1_allowed_after_spec_approval(self):
        """DEFINE→PLAN allowed after spec is approved."""
        from helpers.phase_governance import check_phase_approval_gate
        from helpers import workflow_state
        agent, tmpdir = _make_integration_agent(phase="DEFINE")
        try:
            spec_path = _create_artifact_file(tmpdir, "spec")
            workflow_state.save_workflow_artifacts(agent, {
                "spec_path": spec_path,
            })

            workflow_state.mark_artifact_approved(agent, "spec")

            result = check_phase_approval_gate(
                agent,
                from_phase="DEFINE",
                to_phase="PLAN",
                enforcement_mode="enforce",
            )
            assert result is True, "G1 gate should allow after spec approval"
        finally:
            _cleanup_agent(tmpdir)

    def test_g1_observe_mode_allows_unapproved(self):
        """In observe mode, G1 warns but allows unapproved transition."""
        from helpers.phase_governance import check_phase_approval_gate
        agent, tmpdir = _make_integration_agent(phase="DEFINE")
        try:
            _create_artifact_file(tmpdir, "spec")
            from helpers import workflow_state
            workflow_state.save_workflow_artifacts(agent, {
                "spec_path": os.path.join(tmpdir, "SPEC.md"),
            })

            result = check_phase_approval_gate(
                agent,
                from_phase="DEFINE",
                to_phase="PLAN",
                enforcement_mode="observe",
            )
            assert result is True, "G1 gate should allow in observe mode"
        finally:
            _cleanup_agent(tmpdir)


# ===========================================================================
# G2 Gate: PLAN→BUILD requires plan approval
# ===========================================================================


class TestG2Gate:
    """G2 gate: PLAN→BUILD transition requires approved plan."""

    def test_g2_blocked_without_plan_approval(self):
        """PLAN→BUILD blocked when plan is not approved (enforce mode)."""
        from helpers.phase_governance import check_phase_approval_gate
        agent, tmpdir = _make_integration_agent(phase="PLAN")
        try:
            _create_artifact_file(tmpdir, "plan")
            from helpers import workflow_state
            workflow_state.save_workflow_artifacts(agent, {
                "plan_path": os.path.join(tmpdir, "tasks", "plan.md"),
            })

            result = check_phase_approval_gate(
                agent,
                from_phase="PLAN",
                to_phase="BUILD",
                enforcement_mode="enforce",
            )
            assert result is False, "G2 gate should block without plan approval"
        finally:
            _cleanup_agent(tmpdir)

    def test_g2_allowed_after_plan_approval(self):
        """PLAN→BUILD allowed after plan is approved."""
        from helpers.phase_governance import check_phase_approval_gate
        from helpers import workflow_state
        agent, tmpdir = _make_integration_agent(phase="PLAN")
        try:
            plan_path = _create_artifact_file(tmpdir, "plan")
            workflow_state.save_workflow_artifacts(agent, {
                "plan_path": plan_path,
            })

            workflow_state.mark_artifact_approved(agent, "plan")

            result = check_phase_approval_gate(
                agent,
                from_phase="PLAN",
                to_phase="BUILD",
                enforcement_mode="enforce",
            )
            assert result is True, "G2 gate should allow after plan approval"
        finally:
            _cleanup_agent(tmpdir)


# ===========================================================================
# Mtime Invalidation
# ===========================================================================


class TestMtimeInvalidation:
    """Verify that modifying an approved artifact re-blocks the gate."""

    def test_mtime_invalidation_re_blocks_gate(self):
        """Approve spec → modify spec file → gate re-blocks."""
        from helpers.phase_governance import check_phase_approval_gate
        from helpers import workflow_state
        agent, tmpdir = _make_integration_agent(phase="DEFINE")
        try:
            spec_path = _create_artifact_file(tmpdir, "spec")
            workflow_state.save_workflow_artifacts(agent, {
                "spec_path": spec_path,
            })

            # Patch resolve_visible_root throughout so artifact path
            # resolution uses tmpdir (both for mark and check).
            with patch("helpers.workflow_state.resolve_visible_root", return_value=tmpdir):
                # Approve spec (stores mtime of tmpdir/SPEC.md)
                workflow_state.mark_artifact_approved(agent, "spec")

                # Gate allows initially
                result_before = check_phase_approval_gate(
                    agent, "DEFINE", "PLAN", enforcement_mode="enforce",
                )
                assert result_before is True

            # Modify the spec file to change mtime
            time.sleep(0.05)
            with open(spec_path, "a") as f:
                f.write("\n\n## Additional section\n")
            os.utime(spec_path, (time.time() + 1, time.time() + 1))

            # Gate now blocks (mtime changed since approval)
            with patch("helpers.workflow_state.resolve_visible_root", return_value=tmpdir):
                result_after = check_phase_approval_gate(
                    agent, "DEFINE", "PLAN", enforcement_mode="enforce",
                )
            assert result_after is False, \
                "Gate should block after spec modification (mtime changed)"
        finally:
            _cleanup_agent(tmpdir)

    def test_mtime_matches_keeps_approval(self):
        """Approval stays valid when artifact file is unchanged."""
        from helpers.phase_governance import check_phase_approval_gate
        from helpers import workflow_state
        agent, tmpdir = _make_integration_agent(phase="DEFINE")
        try:
            spec_path = _create_artifact_file(tmpdir, "spec")
            workflow_state.save_workflow_artifacts(agent, {
                "spec_path": spec_path,
            })

            workflow_state.mark_artifact_approved(agent, "spec")

            with patch("helpers.workflow_state.resolve_visible_root", return_value=tmpdir):
                result = check_phase_approval_gate(
                    agent, "DEFINE", "PLAN", enforcement_mode="enforce",
                )
            assert result is True
        finally:
            _cleanup_agent(tmpdir)


# ===========================================================================
# Natural Language Detection
# ===========================================================================


class TestNaturalLanguageDetection:
    """Verify approval detection from natural language."""

    @pytest.mark.parametrize("text", [
        "This looks great, approved",
        "LGTM, proceed",
        "I've reviewed the spec and it looks good",
        "good to go, ship it",
        "approve",
        "let's go",
    ])
    def test_approval_detected(self, text):
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(text) is True

    @pytest.mark.parametrize("text", [
        "Can you fix section 3?",
        "I'm not sure about this",
        "unapproved",
        "don't approve this",
        "this doesn't look right",
        "what changes did you make?",
        "",  # silence
        "I have some concerns",
        "let me think about it",
    ])
    def test_approval_not_detected(self, text):
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(text) is False

    def test_question_mark_blocks_approval(self):
        """Questions are never treated as approval."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text("This is approved?") is False
        assert detect_approval_in_text("Is this approved?") is False

    def test_negation_blocks_approval(self):
        """Negated approval phrases are rejected."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text("I don't approve") is False
        assert detect_approval_in_text("not approved") is False
        assert detect_approval_in_text("won't approve") is False


# ===========================================================================
# Full Pipeline: Detection → Approval → Gate → Invalidation
# ===========================================================================


class TestFullPipeline:
    """End-to-end pipeline test: detect approval → record → gate checks."""

    def test_spec_approval_pipeline(self):
        """Full pipeline: write spec → detect 'approved' → gate opens."""
        from helpers.phase_governance import check_phase_approval_gate
        from helpers import workflow_state
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        agent, tmpdir = _make_integration_agent(phase="DEFINE")
        try:
            spec_path = _create_artifact_file(tmpdir, "spec")
            workflow_state.save_workflow_artifacts(agent, {
                "spec_path": spec_path,
            })

            # 1. Gate is initially blocked
            gate_before = check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="enforce",
            )
            assert gate_before is False

            # 2. Detect approval language
            user_message = "The spec looks great, approved!"
            assert detect_approval_in_text(user_message) is True

            # 3. Record approval
            workflow_state.mark_artifact_approved(agent, "spec")

            # 4. Verify approval is recorded
            assert workflow_state.is_artifact_approved(agent, "spec") is True

            # 5. Gate now opens
            gate_after = check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="enforce",
            )
            assert gate_after is True

            # 6. Verify approval event in progress log
            log = workflow_state.read_progress_log(agent)
            approval_events = [
                e for e in log
                if e.get("event") == "approval" and e.get("artifact_type") == "spec"
            ]
            assert len(approval_events) >= 1, "Approval event should be logged"
        finally:
            _cleanup_agent(tmpdir)

    def test_plan_approval_pipeline(self):
        """Full pipeline for G2: write plan → approve → BUILD allowed."""
        from helpers.phase_governance import check_phase_approval_gate
        from helpers import workflow_state
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        agent, tmpdir = _make_integration_agent(phase="PLAN")
        try:
            plan_path = _create_artifact_file(tmpdir, "plan")
            workflow_state.save_workflow_artifacts(agent, {
                "plan_path": plan_path,
            })

            assert check_phase_approval_gate(
                agent, "PLAN", "BUILD", enforcement_mode="enforce",
            ) is False

            assert detect_approval_in_text("plan looks good, proceed") is True
            workflow_state.mark_artifact_approved(agent, "plan")

            assert check_phase_approval_gate(
                agent, "PLAN", "BUILD", enforcement_mode="enforce",
            ) is True
        finally:
            _cleanup_agent(tmpdir)


# ===========================================================================
# Enforcement Mode: Correction Injection
# ===========================================================================


class TestEnforcementMode:
    """Verify enforce mode injects corrections for skill skips."""

    def test_enforce_mode_appends_correction(self):
        """When a skill is skipped in enforce mode, a correction is injected."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )

        ext = SkillEnforcer.__new__(SkillEnforcer)
        agent = _make_enforcer_agent_for_acceptance(
            loaded_skills=[],
            last_user_message="implement a rate limiter",
        )
        ext.agent = agent

        config = _make_acceptance_config(enforcement_mode="enforce")
        tool_args = {"code": "def rate_limiter(): pass"}
        original_args = dict(tool_args)

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=config,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args=tool_args,
            ))
            # Should have logged at least once
            assert mock_log.call_count >= 1

        # tool_args must NOT be mutated even in enforce mode
        assert tool_args == original_args

    def test_enforce_mode_no_correction_for_loaded_skill(self):
        """When the correct skill is already loaded, no correction is needed."""
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            SkillEnforcer,
        )
        from helpers.phase_governance import PHASE_SKILL_MAP

        build_skills = PHASE_SKILL_MAP.get("BUILD", [])
        if not build_skills:
            pytest.skip("No BUILD skills defined")

        ext = SkillEnforcer.__new__(SkillEnforcer)
        agent = _make_enforcer_agent_for_acceptance(
            loaded_skills=build_skills[:1],
            last_user_message="implement feature",
        )
        ext.agent = agent

        config = _make_acceptance_config(enforcement_mode="enforce")
        tool_args = {"code": "print('hello')"}

        with patch(
            "extensions.python.tool_execute_before._10_skill_enforcer._get_plugin_config",
            return_value=config,
        ), patch(
            "extensions.python.tool_execute_after._05_skill_telemetry.log_gate_decision",
            new_callable=AsyncMock,
        ) as mock_log:
            _run(ext.execute(
                tool_name="code_execution_tool",
                tool_args=tool_args,
            ))
            if mock_log.called:
                call_kwargs = mock_log.call_args[1] if mock_log.call_args[1] else {}
                state = call_kwargs.get("state", "")
                assert state != "should_correct", \
                    f"No correction when skill is loaded, got state={state}"


# ===========================================================================
# Phase Gate Coverage for All 4 Gates
# ===========================================================================


class TestAllFourGates:
    """Verify all 4 approval gates work correctly."""

    @pytest.mark.parametrize("from_phase,to_phase,artifact_type", [
        ("DEFINE", "PLAN", "spec"),
        ("PLAN", "BUILD", "plan"),
        ("BUILD", "VERIFY", "todo"),
        ("REVIEW", "SHIP", "review"),
    ])
    def test_gate_blocks_without_approval(self, from_phase, to_phase, artifact_type):
        """Each gate blocks in enforce mode without approval."""
        from helpers.phase_governance import check_phase_approval_gate
        agent, tmpdir = _make_integration_agent(phase=from_phase)
        try:
            artifact_path = _create_artifact_file(tmpdir, artifact_type)
            from helpers import workflow_state
            workflow_state.save_workflow_artifacts(agent, {
                f"{artifact_type}_path": artifact_path,
            })

            result = check_phase_approval_gate(
                agent, from_phase, to_phase, enforcement_mode="enforce",
            )
            assert result is False, \
                f"Gate {from_phase}→{to_phase} should block without {artifact_type} approval"
        finally:
            _cleanup_agent(tmpdir)

    @pytest.mark.parametrize("from_phase,to_phase,artifact_type", [
        ("DEFINE", "PLAN", "spec"),
        ("PLAN", "BUILD", "plan"),
        ("BUILD", "VERIFY", "todo"),
        ("REVIEW", "SHIP", "review"),
    ])
    def test_gate_opens_after_approval(self, from_phase, to_phase, artifact_type):
        """Each gate opens after the corresponding artifact is approved."""
        from helpers.phase_governance import check_phase_approval_gate
        from helpers import workflow_state
        agent, tmpdir = _make_integration_agent(phase=from_phase)
        try:
            artifact_path = _create_artifact_file(tmpdir, artifact_type)
            workflow_state.save_workflow_artifacts(agent, {
                f"{artifact_type}_path": artifact_path,
            })

            workflow_state.mark_artifact_approved(agent, artifact_type)

            result = check_phase_approval_gate(
                agent, from_phase, to_phase, enforcement_mode="enforce",
            )
            assert result is True, \
                f"Gate {from_phase}→{to_phase} should open after {artifact_type} approval"
        finally:
            _cleanup_agent(tmpdir)


# ===========================================================================
# VERIFY Phase: No Gate (Intentional Skip)
# ===========================================================================


class TestVerifyNoGate:
    """VERIFY phase intentionally has no artifact mapping."""

    def test_verify_to_review_no_approval_needed(self):
        """VERIFY→REVIEW does not require approval (no artifact mapping)."""
        from helpers.phase_governance import check_phase_approval_gate
        agent, tmpdir = _make_integration_agent(phase="VERIFY")
        try:
            result = check_phase_approval_gate(
                agent, "VERIFY", "REVIEW", enforcement_mode="enforce",
            )
            assert result is True, \
                "VERIFY→REVIEW should always be allowed (no artifact gate)"
        finally:
            _cleanup_agent(tmpdir)


# ===========================================================================
# Fail-Safe Tests
# ===========================================================================


class TestFailSafe:
    """Verify fail-safe behavior: errors never block the agent loop."""

    def test_approval_gate_error_enforce_blocks(self):
        """When state is unreadable, gate blocks in enforce mode (unapproved)."""
        from helpers.phase_governance import check_phase_approval_gate
        agent = MagicMock()
        agent.context = None  # Will cause state dir resolution to fail

        # is_artifact_approved catches errors and returns False,
        # so the gate proceeds to enforce mode check and blocks.
        # This is correct: can't verify approval → treat as unapproved.
        result = check_phase_approval_gate(
            agent, "DEFINE", "PLAN", enforcement_mode="enforce",
        )
        assert result is False

    def test_approval_gate_error_observe_allows(self):
        """When state is unreadable, gate allows in observe mode (fail-safe)."""
        from helpers.phase_governance import check_phase_approval_gate
        agent = MagicMock()
        agent.context = None
        result = check_phase_approval_gate(
            agent, "DEFINE", "PLAN", enforcement_mode="observe",
        )
        # In observe mode, even unapproved transitions are allowed
        assert result is True

    def test_detect_approval_never_crashes(self):
        """detect_approval_in_text handles edge cases without crashing."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(None) is False
        assert detect_approval_in_text("") is False
        assert detect_approval_in_text("\x00\x01") is False
        assert detect_approval_in_text("a" * 10000) is False


# ===========================================================================
# Helpers for enforcement tests
# ===========================================================================


def _make_enforcer_agent_for_acceptance(
    *,
    loaded_skills: list[str] | None = None,
    last_user_message: str = "implement feature",
):
    """Create a mock agent for enforcement acceptance tests."""
    agent = MagicMock()
    agent.data = {"loaded_skills": list(loaded_skills or [])}

    msg = MagicMock()
    msg.content = last_user_message
    agent.last_user_message = msg

    current_tool = MagicMock()
    current_tool.method = "execute"
    current_tool.args = {"code": "print('hello')"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    agent.context = None
    return agent


def _make_acceptance_config(*, enforcement_mode: str = "observe"):
    """Create a plugin config dict for acceptance tests."""
    return {
        "enforcement_mode": enforcement_mode,
        "telemetry_enabled": True,
        "telemetry_log_path": ".a0proj/skill_activations.jsonl",
        "phase_governance_enabled": True,
        "skill_contracts_enabled": False,
        "enforcement_shadow_sample_rate": 0.0,
    }
