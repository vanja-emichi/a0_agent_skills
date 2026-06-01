# Tests for helpers/phase_governance.py — phase model, transitions, and deduplication.
#
# Covers:
# - PHASE_ORDER and PHASE_SKILL_MAP constants
# - get_expected_skills for all 6 phases + invalid
# - get_phase_for_skill reverse lookup
# - is_phase_valid_transition: initial, forward, rewind, jump, reentry, invalid
# - get_current_phase with mock agent
# - transition_phase with mock agent
# - get_last_correction_for_context
# - should_suppress_correction (cooldown logic)

from __future__ import annotations

import importlib
import importlib.util
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Module loader — load phase_governance.py via importlib
# ---------------------------------------------------------------------------

_pg_module = None


def _load_phase_governance():
    """Load helpers.phase_governance via importlib from plugin root."""
    global _pg_module
    if _pg_module is not None:
        sys.modules["helpers.phase_governance"] = _pg_module
        return _pg_module

    plugin_root = Path(__file__).parent.parent
    pg_path = plugin_root / "helpers" / "phase_governance.py"
    assert pg_path.exists(), f"phase_governance.py not found at {pg_path}"

    spec = importlib.util.spec_from_file_location(
        "helpers.phase_governance", str(pg_path)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules["helpers.phase_governance"] = mod
    _pg_module = mod
    return mod


@pytest.fixture(autouse=True)
def _setup_pg_module():
    """Ensure the phase_governance module is loaded before each test."""
    _load_phase_governance()


# ===========================================================================
# Constants
# ===========================================================================


class TestPhaseOrder:
    """PHASE_ORDER constant tests."""

    def test_phase_order_has_six_phases(self):
        pg = _load_phase_governance()
        assert len(pg.PHASE_ORDER) == 6

    def test_phase_order_sequence(self):
        pg = _load_phase_governance()
        assert pg.PHASE_ORDER == [
            "DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP",
        ]


class TestPhaseSkillMap:
    """PHASE_SKILL_MAP constant tests."""

    def test_all_phases_have_skills(self):
        pg = _load_phase_governance()
        for phase in pg.PHASE_ORDER:
            assert phase in pg.PHASE_SKILL_MAP, f"Missing skill map for {phase}"
            assert len(pg.PHASE_SKILL_MAP[phase]) > 0, f"Empty skill list for {phase}"

    def test_define_skills(self):
        pg = _load_phase_governance()
        assert pg.PHASE_SKILL_MAP["DEFINE"] == [
            "interview-me",
            "spec-driven-development",
            "idea-refine",
        ]

    def test_plan_skills(self):
        pg = _load_phase_governance()
        assert pg.PHASE_SKILL_MAP["PLAN"] == [
            "planning-and-task-breakdown",
            "context-engineering",
        ]

    def test_build_skills(self):
        pg = _load_phase_governance()
        expected = [
            "incremental-implementation",
            "test-driven-development",
            "source-driven-development",
            "doubt-driven-development",
            "frontend-ui-engineering",
            "api-and-interface-design",
        ]
        assert pg.PHASE_SKILL_MAP["BUILD"] == expected

    def test_verify_skills(self):
        pg = _load_phase_governance()
        assert pg.PHASE_SKILL_MAP["VERIFY"] == [
            "browser-testing-with-devtools",
            "debugging-and-error-recovery",
        ]

    def test_review_skills(self):
        pg = _load_phase_governance()
        expected = [
            "code-review-and-quality",
            "code-simplification",
            "security-and-hardening",
            "performance-optimization",
        ]
        assert pg.PHASE_SKILL_MAP["REVIEW"] == expected

    def test_ship_skills(self):
        pg = _load_phase_governance()
        expected = [
            "shipping-and-launch",
            "ci-cd-and-automation",
            "git-workflow-and-versioning",
            "documentation-and-adrs",
            "deprecation-and-migration",
        ]
        assert pg.PHASE_SKILL_MAP["SHIP"] == expected


# ===========================================================================
# get_expected_skills
# ===========================================================================


class TestGetExpectedSkills:
    """get_expected_skills() returns correct skill lists."""

    def test_define(self):
        pg = _load_phase_governance()
        skills = pg.get_expected_skills("DEFINE")
        assert "spec-driven-development" in skills
        assert "interview-me" in skills

    def test_plan(self):
        pg = _load_phase_governance()
        skills = pg.get_expected_skills("PLAN")
        assert "planning-and-task-breakdown" in skills

    def test_build(self):
        pg = _load_phase_governance()
        skills = pg.get_expected_skills("BUILD")
        assert "test-driven-development" in skills
        assert "incremental-implementation" in skills

    def test_verify(self):
        pg = _load_phase_governance()
        skills = pg.get_expected_skills("VERIFY")
        assert "debugging-and-error-recovery" in skills

    def test_review(self):
        pg = _load_phase_governance()
        skills = pg.get_expected_skills("REVIEW")
        assert "code-review-and-quality" in skills

    def test_ship(self):
        pg = _load_phase_governance()
        skills = pg.get_expected_skills("SHIP")
        assert "shipping-and-launch" in skills

    def test_invalid_phase_returns_empty(self):
        pg = _load_phase_governance()
        assert pg.get_expected_skills("INVALID") == []

    def test_empty_string_returns_empty(self):
        pg = _load_phase_governance()
        assert pg.get_expected_skills("") == []

    def test_returns_copy_not_reference(self):
        pg = _load_phase_governance()
        s1 = pg.get_expected_skills("BUILD")
        s2 = pg.get_expected_skills("BUILD")
        assert s1 == s2
        assert s1 is not s2  # Different list objects


# ===========================================================================
# get_phase_for_skill
# ===========================================================================


class TestGetPhaseForSkill:
    """get_phase_for_skill() reverse lookup tests."""

    def test_known_skill(self):
        pg = _load_phase_governance()
        assert pg.get_phase_for_skill("test-driven-development") == "BUILD"

    def test_define_skill(self):
        pg = _load_phase_governance()
        assert pg.get_phase_for_skill("interview-me") == "DEFINE"

    def test_ship_skill(self):
        pg = _load_phase_governance()
        assert pg.get_phase_for_skill("shipping-and-launch") == "SHIP"

    def test_unknown_skill(self):
        pg = _load_phase_governance()
        assert pg.get_phase_for_skill("nonexistent-skill") is None


# ===========================================================================
# is_phase_valid_transition
# ===========================================================================


class TestIsPhaseValidTransition:
    """is_phase_valid_transition() validates all transition types."""

    def test_initial_none_to_define(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition(None, "DEFINE")
        assert result["valid"] is True
        assert result["transition_type"] == "initial"
        assert result["warning"] is None

    def test_jump_none_to_build(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition(None, "BUILD")
        assert result["valid"] is True
        assert result["transition_type"] == "jump"
        assert result["warning"] is not None
        assert "BUILD" in result["warning"]

    def test_jump_none_to_ship(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition(None, "SHIP")
        assert result["valid"] is True
        assert result["transition_type"] == "jump"

    def test_forward_define_to_plan(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("DEFINE", "PLAN")
        assert result["valid"] is True
        assert result["transition_type"] == "forward"
        assert result["warning"] is None

    def test_forward_plan_to_build(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("PLAN", "BUILD")
        assert result["valid"] is True
        assert result["transition_type"] == "forward"

    def test_forward_build_to_verify(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("BUILD", "VERIFY")
        assert result["valid"] is True
        assert result["transition_type"] == "forward"

    def test_forward_verify_to_review(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("VERIFY", "REVIEW")
        assert result["valid"] is True
        assert result["transition_type"] == "forward"

    def test_forward_review_to_ship(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("REVIEW", "SHIP")
        assert result["valid"] is True
        assert result["transition_type"] == "forward"

    def test_forward_skip_multiple(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("DEFINE", "BUILD")
        assert result["valid"] is True
        assert result["transition_type"] == "forward"

    def test_rewind_build_to_define(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("BUILD", "DEFINE")
        assert result["valid"] is True
        assert result["transition_type"] == "rewind"
        assert result["warning"] is not None
        assert "rewind" in result["warning"]

    def test_rewind_ship_to_plan(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("SHIP", "PLAN")
        assert result["valid"] is True
        assert result["transition_type"] == "rewind"

    def test_reentry_same_phase(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("BUILD", "BUILD")
        assert result["valid"] is True
        assert result["transition_type"] == "reentry"
        assert result["warning"] is None

    def test_reentry_define(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("DEFINE", "DEFINE")
        assert result["valid"] is True
        assert result["transition_type"] == "reentry"

    def test_invalid_target_phase(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("BUILD", "INVALID")
        assert result["valid"] is False
        assert result["transition_type"] == "invalid"

    def test_invalid_source_phase(self):
        pg = _load_phase_governance()
        result = pg.is_phase_valid_transition("INVALID", "BUILD")
        assert result["valid"] is False
        assert result["transition_type"] == "invalid"


# ===========================================================================
# get_current_phase
# ===========================================================================


class TestGetCurrentPhase:
    """get_current_phase() reads phase from workflow state."""

    def test_returns_phase_when_present(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read:
            mock_read.return_value = {"phase": "BUILD", "version": 1}
            assert pg.get_current_phase(agent) == "BUILD"

    def test_returns_none_when_no_state(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read:
            mock_read.return_value = None
            assert pg.get_current_phase(agent) is None

    def test_returns_none_when_corrupt(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read:
            mock_read.return_value = {"not_phase": True}
            assert pg.get_current_phase(agent) is None

    def test_returns_none_when_invalid_phase(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read:
            mock_read.return_value = {"phase": "INVALID"}
            assert pg.get_current_phase(agent) is None

    def test_returns_none_on_exception(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read:
            mock_read.side_effect = RuntimeError("boom")
            assert pg.get_current_phase(agent) is None


# ===========================================================================
# transition_phase
# ===========================================================================


class TestTransitionPhase:
    """transition_phase() validates, persists, and logs transitions."""

    def test_initial_transition(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read, \
             patch("helpers.workflow_state.save_current_phase") as mock_save, \
             patch("helpers.workflow_state.append_progress_event") as mock_log:
            mock_read.return_value = None
            mock_save.return_value = "/some/path"

            result = pg.transition_phase(agent, "DEFINE")

            assert result is not None
            assert result["transition_type"] == "initial"
            assert result["valid"] is True
            mock_save.assert_called_once()
            mock_log.assert_called_once()

            # Verify progress event
            event = mock_log.call_args[0][1]
            assert event["event"] == "phase_change"
            assert event["phase"] == "DEFINE"
            assert event["transition_type"] == "initial"

    def test_forward_transition(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read, \
             patch("helpers.workflow_state.save_current_phase") as mock_save, \
             patch("helpers.workflow_state.append_progress_event") as mock_log:
            # First call: get_current_phase reads it
            mock_read.return_value = {"phase": "DEFINE", "phases_completed": []}
            mock_save.return_value = "/some/path"

            result = pg.transition_phase(agent, "PLAN")

            assert result is not None
            assert result["transition_type"] == "forward"

            # Verify phases_completed includes DEFINE
            save_data = mock_save.call_args[0][1]
            assert "DEFINE" in save_data["phases_completed"]

    def test_rewind_transition(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read, \
             patch("helpers.workflow_state.save_current_phase") as mock_save, \
             patch("helpers.workflow_state.append_progress_event") as mock_log:
            mock_read.return_value = {
                "phase": "BUILD",
                "phases_completed": ["DEFINE", "PLAN"],
            }
            mock_save.return_value = "/some/path"

            result = pg.transition_phase(agent, "DEFINE")

            assert result is not None
            assert result["transition_type"] == "rewind"

            # phases_completed should be preserved from existing
            save_data = mock_save.call_args[0][1]
            assert "DEFINE" in save_data["phases_completed"]
            assert "PLAN" in save_data["phases_completed"]

    def test_invalid_phase_returns_none(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read:
            mock_read.return_value = None
            result = pg.transition_phase(agent, "INVALID")
            assert result is None

    def test_save_failure_returns_none(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_current_phase") as mock_read, \
             patch("helpers.workflow_state.save_current_phase") as mock_save:
            mock_read.return_value = None
            mock_save.return_value = None  # Save failed

            result = pg.transition_phase(agent, "DEFINE")
            assert result is None

    def test_exception_returns_none(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        agent.data = {}
        with patch("helpers.workflow_state.read_current_phase") as mock_read, \
             patch("helpers.workflow_state.save_current_phase") as mock_save:
            mock_read.return_value = None
            mock_save.side_effect = RuntimeError("disk full")
            result = pg.transition_phase(agent, "DEFINE")
            assert result is None


# ===========================================================================
# get_last_correction_for_context
# ===========================================================================


class TestGetLastCorrectionForContext:
    """get_last_correction_for_context() reads progress log for corrections."""

    def test_no_progress_log_returns_none(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = []
            result = pg.get_last_correction_for_context(agent, "code_execution_tool", "tdd")
            assert result is None

    def test_unrelated_events_returns_none(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "phase_change", "phase": "BUILD"},
                {"event": "skill_loaded", "skill": "tdd"},
            ]
            result = pg.get_last_correction_for_context(agent, "code_execution_tool", "tdd")
            assert result is None

    def test_matching_correction_returns_event(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        now = time.time()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": now},
            ]
            result = pg.get_last_correction_for_context(agent, "code_execution_tool", "tdd")
            assert result is not None
            assert result["candidate"] == "tdd"

    def test_multiple_corrections_returns_most_recent(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        old_ts = time.time() - 600
        new_ts = time.time() - 100
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": old_ts},
                {"event": "gate_correction", "candidate": "tdd", "ts": new_ts},
            ]
            result = pg.get_last_correction_for_context(agent, "code_execution_tool", "tdd")
            assert result is not None
            assert result["ts"] == new_ts

    def test_different_candidate_returns_none(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        now = time.time()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "other-skill", "ts": now},
            ]
            result = pg.get_last_correction_for_context(agent, "code_execution_tool", "tdd")
            assert result is None

    def test_exception_returns_none(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.side_effect = RuntimeError("boom")
            result = pg.get_last_correction_for_context(agent, "code_execution_tool", "tdd")
            assert result is None


# ===========================================================================
# should_suppress_correction
# ===========================================================================


class TestShouldSuppressCorrection:
    """should_suppress_correction() checks cooldown window."""

    def test_no_prior_corrections_returns_false(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = []
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is False

    def test_recent_correction_within_cooldown_returns_true(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        now = time.time()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": now - 60},
            ]
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is True

    def test_old_correction_outside_cooldown_returns_false(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        old_ts = time.time() - 600  # 10 minutes ago
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": old_ts},
            ]
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is False

    def test_correction_for_different_candidate_returns_false(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        now = time.time()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "other-skill", "ts": now - 60},
            ]
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is False

    def test_exactly_at_cooldown_boundary_returns_false(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        # Exactly 300 seconds ago — elapsed == cooldown, so NOT within cooldown
        boundary_ts = time.time() - 300.0
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": boundary_ts},
            ]
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is False

    def test_just_inside_cooldown_returns_true(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        # 299 seconds ago — just inside cooldown
        ts = time.time() - 299.0
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": ts},
            ]
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is True

    def test_custom_cooldown_seconds(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        ts = time.time() - 50  # 50 seconds ago
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": ts},
            ]
            # 60 second cooldown → 50 < 60 → suppressed
            assert pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=60.0,
            ) is True
            # 30 second cooldown → 50 > 30 → NOT suppressed
            assert pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=30.0,
            ) is False

    def test_exception_returns_false(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch.object(
            pg, "get_last_correction_for_context", side_effect=RuntimeError("boom")
        ):
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is False

    def test_malformed_ts_returns_false(self):
        pg = _load_phase_governance()
        agent = MagicMock()
        with patch("helpers.workflow_state.read_progress_log") as mock_read:
            mock_read.return_value = [
                {"event": "gate_correction", "candidate": "tdd", "ts": "not-a-number"},
            ]
            result = pg.should_suppress_correction(
                agent, "code_execution_tool", "tdd", cooldown_seconds=300.0,
            )
            assert result is False
