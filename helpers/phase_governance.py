"""Phase-aware workflow governance helper.

Owns the phase model, phase-skill mapping, transition validation,
and correction deduplication logic.

State I/O is delegated to helpers.workflow_state — this module
never touches state files directly.

All public functions are fail-safe: exceptions return safe defaults.
"""

from __future__ import annotations

import logging
import time
from typing import Any

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Phase model constants
# ---------------------------------------------------------------------------

PHASE_ORDER: list[str] = [
    "DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP",
]

PHASE_SKILL_MAP: dict[str, list[str]] = {
    "DEFINE": [
        "interview-me",
        "spec-driven-development",
        "idea-refine",
    ],
    "PLAN": [
        "planning-and-task-breakdown",
        "context-engineering",
    ],
    "BUILD": [
        "incremental-implementation",
        "test-driven-development",
        "source-driven-development",
        "doubt-driven-development",
        "frontend-ui-engineering",
        "api-and-interface-design",
    ],
    "VERIFY": [
        "browser-testing-with-devtools",
        "debugging-and-error-recovery",
    ],
    "REVIEW": [
        "code-review-and-quality",
        "code-simplification",
        "security-and-hardening",
        "performance-optimization",
    ],
    "SHIP": [
        "shipping-and-launch",
        "ci-cd-and-automation",
        "git-workflow-and-versioning",
        "documentation-and-adrs",
        "deprecation-and-migration",
    ],
    "META": [
        "using-agent-skills",
    ],
}

# Reverse map: skill name -> phase name (for quick lookup)
_SKILL_TO_PHASE: dict[str, str] = {}
for _phase, _skills in PHASE_SKILL_MAP.items():
    for _skill in _skills:
        _SKILL_TO_PHASE[_skill] = _phase

# Phase → artifact type mapping for approval gates.
# Only phases with approval gates are listed.
# VERIFY is intentionally absent (no artifact to approve).
PHASE_ARTIFACT_MAP: dict[str, str] = {
    "DEFINE": "spec",
    "PLAN": "plan",
    "BUILD": "todo",
    "REVIEW": "review",
    "SHIP": "report",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_current_phase(agent) -> str | None:
    """Return the current phase name, or None if unknown."""
    try:
        from helpers import workflow_state
        phase_data = workflow_state.read_current_phase(agent)
        if isinstance(phase_data, dict):
            phase = phase_data.get("phase")
            if isinstance(phase, str) and phase in PHASE_ORDER:
                return phase
    except Exception:
        _log.debug("Failed to read current phase", exc_info=True)
    return None


def get_expected_skills(phase: str) -> list[str]:
    """Return the list of skill names expected for the given phase.

    Returns an empty list for unknown phases.
    """
    try:
        return list(PHASE_SKILL_MAP.get(phase, []))
    except Exception:
        return []


def get_phase_for_skill(skill_name: str) -> str | None:
    """Return the phase that a skill belongs to, or None."""
    try:
        return _SKILL_TO_PHASE.get(skill_name)
    except Exception:
        return None


def is_phase_valid_transition(
    from_phase: str | None, to_phase: str,
) -> dict:
    """Validate a phase transition.

    Returns::
        {
            "valid": bool,
            "transition_type": str,  # forward, rewind, reentry, jump, initial
            "warning": str | None     # non-null for rewinds and jumps
        }
    """
    try:
        # Validate target phase
        if to_phase not in PHASE_ORDER:
            return {
                "valid": False,
                "transition_type": "invalid",
                "warning": f"Unknown phase: {to_phase!r}",
            }

        # Initial entry (no previous phase)
        if from_phase is None:
            if to_phase == "DEFINE":
                return {
                    "valid": True,
                    "transition_type": "initial",
                    "warning": None,
                }
            else:
                return {
                    "valid": True,
                    "transition_type": "jump",
                    "warning": f"Jump-start to {to_phase} detected (expected DEFINE first)",
                }

        # Validate from_phase
        if from_phase not in PHASE_ORDER:
            return {
                "valid": False,
                "transition_type": "invalid",
                "warning": f"Unknown source phase: {from_phase!r}",
            }

        # Reentry (same phase)
        if from_phase == to_phase:
            return {
                "valid": True,
                "transition_type": "reentry",
                "warning": None,
            }

        from_idx = PHASE_ORDER.index(from_phase)
        to_idx = PHASE_ORDER.index(to_phase)

        if to_idx > from_idx:
            # Forward transition
            return {
                "valid": True,
                "transition_type": "forward",
                "warning": None,
            }
        else:
            # Rewind (backward transition)
            return {
                "valid": True,
                "transition_type": "rewind",
                "warning": f"Phase rewind from {from_phase} to {to_phase}",
            }
    except Exception as exc:
        return {
            "valid": False,
            "transition_type": "error",
            "warning": f"Transition validation error: {exc}",
        }


def transition_phase(agent, new_phase: str) -> dict | None:
    """Execute a phase transition: validate, update state, log progress.

    Returns transition info dict or None on failure.
    """
    try:
        from helpers import workflow_state

        # Validate the transition
        current = get_current_phase(agent)
        info = is_phase_valid_transition(current, new_phase)

        if not info["valid"]:
            _log.warning("Invalid phase transition: %s -> %s: %s",
                         current, new_phase, info.get("warning"))
            return None

        # Build phase data
        phase_data = {
            "phase": new_phase,
            "phases_completed": [],
            "transition_from": current,
            "transition_type": info["transition_type"],
        }

        # Compute phases_completed
        if current is not None and current in PHASE_ORDER:
            from_idx = PHASE_ORDER.index(current)
            to_idx = PHASE_ORDER.index(new_phase)
            if to_idx > from_idx:
                # Forward: mark everything up to (but not including) new_phase as completed
                completed = PHASE_ORDER[:to_idx]
            else:
                # Rewind or reentry: keep existing completed phases
                try:
                    existing = workflow_state.read_current_phase(agent) or {}
                    completed = existing.get("phases_completed", [])
                except Exception:
                    completed = []
            phase_data["phases_completed"] = completed
        elif current is None and new_phase == "DEFINE":
            phase_data["phases_completed"] = []
        elif current is None:
            # Jump: assume all phases before new_phase are completed
            new_idx = PHASE_ORDER.index(new_phase)
            phase_data["phases_completed"] = PHASE_ORDER[:new_idx]

        # Persist
        saved = workflow_state.save_current_phase(agent, phase_data)
        if saved is None:
            _log.warning("Failed to persist phase transition")
            return None

        # Log progress event
        workflow_state.append_progress_event(agent, {
            "event": "phase_change",
            "phase": new_phase,
            "transition_from": current,
            "transition_type": info["transition_type"],
        })

        return info
    except Exception as exc:
        _log.debug("Phase transition failed: %s", exc, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Approval gate (Task 2 — Phase Gate Check)
# ---------------------------------------------------------------------------


def check_phase_approval_gate(
    agent,
    from_phase: str | None,
    to_phase: str,
    enforcement_mode: str = "observe",
) -> bool:
    """Check whether a forward phase transition should be allowed.

    Returns True if the transition may proceed, False if it should be
    blocked because the *from* phase's artifact has not been approved.

    Rules:
    - Only forward transitions from phases with an artifact mapping are
      gated.  Reentry, rewind, and initial/jump entries are always allowed.
    - In **enforce** mode the gate *blocks* unapproved transitions.
    - In **observe** mode the gate *allows* unapproved transitions but logs
      a warning.
    - On any error the gate returns True (fail-safe: never break the agent
      loop).

    Args:
        agent: The agent instance (passed through to ``is_artifact_approved``).
        from_phase: The current phase name, or ``None`` for initial entry.
        to_phase: The target phase name.
        enforcement_mode: ``"enforce"`` or ``"observe"`` (default ``"observe"``).

    Returns:
        True to allow the transition, False to block it.
    """
    try:
        # --- Fast exits: transitions that never need approval ---

        # Invalid target phase → allow (fail-safe)
        if to_phase not in PHASE_ORDER:
            return True

        # Initial entry / jump (from_phase is None) → no gate
        if from_phase is None:
            return True

        # Invalid source phase → allow (fail-safe)
        if from_phase not in PHASE_ORDER:
            return True

        # Only forward transitions are gated
        from_idx = PHASE_ORDER.index(from_phase)
        to_idx = PHASE_ORDER.index(to_phase)
        if to_idx <= from_idx:
            # Reentry or rewind → no gate
            return True

        # --- Check if the *from* phase has an artifact mapping ---
        artifact_type = PHASE_ARTIFACT_MAP.get(from_phase)
        if artifact_type is None:
            # Phase has no artifact (e.g. VERIFY) → no gate
            return True

        # --- Query approval state ---
        from helpers import workflow_state
        approved = workflow_state.is_artifact_approved(agent, artifact_type)

        if approved:
            return True

        # --- Unapproved: behavior depends on enforcement mode ---
        if enforcement_mode == "enforce":
            _log.warning(
                "Phase gate BLOCKED %s→%s: %s not approved (enforce mode)",
                from_phase, to_phase, artifact_type,
            )
            return False
        else:
            # observe or unknown mode → warn but allow
            _log.warning(
                "Phase gate: %s→%s transition without approved %s "
                "(%s mode — allowed)",
                from_phase, to_phase, artifact_type, enforcement_mode,
            )
            return True

    except Exception as exc:
        # Fail-safe depends on enforcement mode:
        # - enforce: deny by default (never bypass the gate on errors)
        # - observe: allow by default (fail-safe doesn't block)
        _log.warning("Approval gate check failed: %s", exc, exc_info=True)
        if enforcement_mode == "enforce":
            return False
        return True


# ---------------------------------------------------------------------------
# Correction deduplication (Task 2)
# ---------------------------------------------------------------------------


def get_last_correction_for_context(
    agent, tool_name: str, candidate: str,
) -> dict | None:
    """Check if a correction for this candidate was already issued recently.

    Reads progress log and returns the most recent matching gate_correction
    event, or None if no match found.
    """
    try:
        from helpers import workflow_state
        entries = workflow_state.read_progress_log(agent, tail=200)
        # Search backwards for most recent match
        for entry in reversed(entries):
            if entry.get("event") != "gate_correction":
                continue
            if entry.get("candidate") != candidate:
                continue
            return entry
        return None
    except Exception:
        _log.debug("Failed to query correction history", exc_info=True)
        return None


def should_suppress_correction(
    agent,
    tool_name: str,
    candidate: str,
    cooldown_seconds: float = 300.0,
) -> bool:
    """Return True if a recent correction for this candidate/context was
    already issued within the cooldown window.

    Prevents correction loops.  Fail-safe: returns False on any error.
    """
    try:
        last = get_last_correction_for_context(agent, tool_name, candidate)
        if last is None:
            return False
        last_ts = last.get("ts", 0)
        if not isinstance(last_ts, (int, float)):
            return False
        elapsed = time.time() - last_ts
        return elapsed < cooldown_seconds
    except Exception:
        _log.debug("Correction suppression check failed", exc_info=True)
        return False