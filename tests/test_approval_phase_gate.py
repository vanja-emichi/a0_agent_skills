"""Tests for the phase gate approval check (Task 2).

Verifies that:
- check_phase_approval_gate blocks unapproved transitions in enforce mode
- check_phase_approval_gate allows transitions when artifact is approved
- check_phase_approval_gate warns but allows in observe mode
- Phases without artifact mappings don't require approval
- Reentry and rewind transitions skip the gate
- Gate is fail-safe (never raises, returns True on error)
- is_artifact_approved reads from workflow_artifacts.json correctly

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_approval_phase_gate.py -v
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
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


# ---------------------------------------------------------------------------
# Helper to create mock agent and approval state
# ---------------------------------------------------------------------------

def _make_agent():
    """Create a minimal mock agent."""
    agent = MagicMock()
    agent.context = None  # Prevent MagicMock file leaks
    return agent


def _approved_state(*artifact_types):
    """Return a workflow_artifacts dict with specified types marked approved."""
    approved = {t: True for t in artifact_types}
    approved_at = {t: 1234567890.0 for t in artifact_types}
    return {"approved": approved, "approved_at": approved_at}


def _unapproved_state():
    """Return a workflow_artifacts dict with nothing approved."""
    return {"approved": {}, "approved_at": {}}


# ===========================================================================
# is_artifact_approved — unit tests for the new workflow_state function
# ===========================================================================


class TestIsArtifactApproved:
    """is_artifact_approved reads the approved dict correctly."""

    def test_returns_true_when_approved(self):
        ws = sys.modules.get("helpers.workflow_state")
        if ws is None or not hasattr(ws, "is_artifact_approved"):
            pytest.skip("is_artifact_approved not in cached module")
        agent = _make_agent()
        with patch.object(ws, "read_workflow_artifacts", return_value=_approved_state("spec")):
            assert ws.is_artifact_approved(agent, "spec") is True

    def test_returns_false_when_not_approved(self):
        ws = sys.modules.get("helpers.workflow_state")
        if ws is None or not hasattr(ws, "is_artifact_approved"):
            pytest.skip("is_artifact_approved not in cached module")
        agent = _make_agent()
        with patch.object(ws, "read_workflow_artifacts", return_value=_unapproved_state()):
            assert ws.is_artifact_approved(agent, "spec") is False

    def test_returns_false_when_no_state(self):
        ws = sys.modules.get("helpers.workflow_state")
        if ws is None or not hasattr(ws, "is_artifact_approved"):
            pytest.skip("is_artifact_approved not in cached module")
        agent = _make_agent()
        with patch.object(ws, "read_workflow_artifacts", return_value=None):
            assert ws.is_artifact_approved(agent, "spec") is False

    def test_returns_false_on_exception(self):
        ws = sys.modules.get("helpers.workflow_state")
        if ws is None or not hasattr(ws, "is_artifact_approved"):
            pytest.skip("is_artifact_approved not in cached module")
        agent = _make_agent()
        with patch.object(ws, "read_workflow_artifacts", side_effect=RuntimeError("boom")):
            assert ws.is_artifact_approved(agent, "spec") is False


# ===========================================================================
# PHASE_ARTIFACT_MAP constant
# ===========================================================================


class TestPhaseArtifactMap:
    """PHASE_ARTIFACT_MAP defines phase → artifact_type mappings."""

    def test_define_maps_to_spec(self):
        pg = _load_phase_governance()
        assert pg.PHASE_ARTIFACT_MAP["DEFINE"] == "spec"

    def test_plan_maps_to_plan(self):
        pg = _load_phase_governance()
        assert pg.PHASE_ARTIFACT_MAP["PLAN"] == "plan"

    def test_build_maps_to_todo(self):
        pg = _load_phase_governance()
        assert pg.PHASE_ARTIFACT_MAP["BUILD"] == "todo"

    def test_review_maps_to_review(self):
        pg = _load_phase_governance()
        assert pg.PHASE_ARTIFACT_MAP["REVIEW"] == "review"

    def test_ship_maps_to_report(self):
        pg = _load_phase_governance()
        assert pg.PHASE_ARTIFACT_MAP["SHIP"] == "report"

    def test_verify_not_in_map(self):
        """VERIFY phase has no approval gate."""
        pg = _load_phase_governance()
        assert "VERIFY" not in pg.PHASE_ARTIFACT_MAP

    def test_all_phases_are_valid(self):
        pg = _load_phase_governance()
        valid_artifact_types = {"spec", "plan", "todo", "review", "report"}
        for phase, artifact in pg.PHASE_ARTIFACT_MAP.items():
            assert artifact in valid_artifact_types, (
                f"Phase {phase} maps to unknown artifact type: {artifact}"
            )


# ===========================================================================
# check_phase_approval_gate — blocked transitions (enforce mode)
# ===========================================================================


class TestApprovalGateBlocked:
    """Gate blocks transition when artifact is NOT approved (enforce mode)."""

    def test_define_to_plan_blocked_without_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="enforce"
            )
            assert result is False
            mock_approved.assert_called_once_with(agent, "spec")

    def test_plan_to_build_blocked_without_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "PLAN", "BUILD", enforcement_mode="enforce"
            )
            assert result is False
            mock_approved.assert_called_once_with(agent, "plan")

    def test_build_to_review_blocked_without_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "BUILD", "REVIEW", enforcement_mode="enforce"
            )
            assert result is False
            mock_approved.assert_called_once_with(agent, "todo")

    def test_review_to_ship_blocked_without_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "REVIEW", "SHIP", enforcement_mode="enforce"
            )
            assert result is False
            mock_approved.assert_called_once_with(agent, "review")


# ===========================================================================
# check_phase_approval_gate — allowed transitions (approved)
# ===========================================================================


class TestApprovalGateAllowed:
    """Gate allows transition when artifact IS approved."""

    def test_define_to_plan_allowed_with_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=True):
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="enforce"
            )
            assert result is True

    def test_plan_to_build_allowed_with_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=True):
            result = pg.check_phase_approval_gate(
                agent, "PLAN", "BUILD", enforcement_mode="enforce"
            )
            assert result is True

    def test_allowed_in_observe_mode_even_without_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False):
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="observe"
            )
            # Observe mode: warn but allow
            assert result is True

    def test_allowed_in_observe_mode_with_approval(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=True):
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="observe"
            )
            assert result is True


# ===========================================================================
# check_phase_approval_gate — phases without artifact mappings
# ===========================================================================


class TestApprovalGateNoMapping:
    """Phases without artifact mappings should skip the gate."""

    def test_verify_to_review_no_gate(self):
        """VERIFY has no artifact mapping — gate should pass."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "VERIFY", "REVIEW", enforcement_mode="enforce"
            )
            assert result is True
            mock_approved.assert_not_called()

    def test_verify_to_review_no_gate_observe(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "VERIFY", "REVIEW", enforcement_mode="observe"
            )
            assert result is True
            mock_approved.assert_not_called()


# ===========================================================================
# check_phase_approval_gate — non-forward transitions
# ===========================================================================


class TestApprovalGateNonForward:
    """Rewind and reentry transitions should skip the gate."""

    def test_reentry_skips_gate(self):
        """Same-phase reentry should not require approval."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "BUILD", "BUILD", enforcement_mode="enforce"
            )
            assert result is True
            mock_approved.assert_not_called()

    def test_rewind_skips_gate(self):
        """Backward transition should not require approval."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "REVIEW", "PLAN", enforcement_mode="enforce"
            )
            assert result is True
            mock_approved.assert_not_called()

    def test_initial_entry_skips_gate(self):
        """Initial entry (from_phase=None) should not require approval."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, None, "DEFINE", enforcement_mode="enforce"
            )
            assert result is True
            mock_approved.assert_not_called()

    def test_jump_entry_skips_gate(self):
        """Jump entry (from_phase=None, non-DEFINE) should not require approval."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, None, "BUILD", enforcement_mode="enforce"
            )
            assert result is True
            mock_approved.assert_not_called()


# ===========================================================================
# check_phase_approval_gate — fail-safe behavior
# ===========================================================================


class TestApprovalGateFailSafe:
    """Gate is fail-safe — errors default to deny in enforce, allow in observe."""

    def test_exception_blocks_in_enforce_mode(self):
        """M-1: Exception in enforce mode should block transition (deny by default)."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", side_effect=RuntimeError("state file corrupt")):
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="enforce"
            )
            # Fail-safe: deny in enforce mode
            assert result is False

    def test_exception_allows_in_observe_mode(self):
        """M-1: Exception in observe mode should allow transition (fail-safe)."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", side_effect=RuntimeError("state file corrupt")):
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="observe"
            )
            # Fail-safe: allow in observe mode
            assert result is True

    def test_unknown_enforcement_mode_allows(self):
        """Unknown enforcement mode should default to allow (fail-safe)."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False):
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="unknown_mode"
            )
            assert result is True

    def test_invalid_target_phase_allows(self):
        """Invalid target phase should allow (fail-safe)."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, "DEFINE", "INVALID", enforcement_mode="enforce"
            )
            assert result is True
            mock_approved.assert_not_called()

    def test_none_source_phase_allows(self):
        """None source phase is an initial entry — allow."""
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False) as mock_approved:
            result = pg.check_phase_approval_gate(
                agent, None, "DEFINE", enforcement_mode="enforce"
            )
            assert result is True
            mock_approved.assert_not_called()


# ===========================================================================
# check_phase_approval_gate — logging verification
# ===========================================================================


class TestApprovalGateLogging:
    """Verify the gate logs appropriate warnings."""

    def test_blocked_transition_logs_warning(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False),              patch.object(pg._log, "warning") as mock_warn:
            pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="enforce"
            )
            assert mock_warn.called

    def test_observe_mode_logs_warning_on_unapproved(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=False),              patch.object(pg._log, "warning") as mock_warn:
            pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="observe"
            )
            assert mock_warn.called

    def test_approved_transition_no_block_warning(self):
        pg = _load_phase_governance()
        ws = sys.modules["helpers.workflow_state"]
        agent = _make_agent()
        with patch.object(ws, "is_artifact_approved", return_value=True),              patch.object(pg._log, "warning") as mock_warn:
            pg.check_phase_approval_gate(
                agent, "DEFINE", "PLAN", enforcement_mode="enforce"
            )
            assert not mock_warn.called
