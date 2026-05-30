"""Skill Enforcer Extension — observe + enforce modes with phase-aware governance.

Fires before target tool execution (code_execution_tool, text_editor).
In observe mode: logs would-fire decisions to telemetry without mutating tool_args.
In enforce mode: runs utility-model classifier and appends corrective warnings
  when a skill should have been loaded.

Phase-aware governance (Slice 3):
  - Reads current workflow phase from state
  - Checks if candidate skill is expected in current phase
  - Suppresses corrections for skills not expected in this phase
  - Deduplicates repeated corrections within a cooldown window
  - Enriches telemetry and correction messages with phase context

Must never raise — all logic is wrapped in a top-level try/except so that
enforcer failures cannot affect normal agent operation.

Configuration keys (default_config.yaml):
  enforcement_mode: observe            # observe | enforce
  enforcement_classifier_model: null   # null = use utility model
  enforcement_shadow_sample_rate: 0.0  # 0.0 = disabled (MVP)
  phase_governance_enabled: true       # Set to false to disable phase-aware enforcement
  enforcement_correction_cooldown_seconds: 300  # Min seconds between same-candidate corrections
"""

from __future__ import annotations

import logging

from helpers.extension import Extension

_log = logging.getLogger(__name__)

# Module-level cache for _import_helpers() — avoids 5 _load_module_by_path
# calls on every execute().  Reset via _reset_helpers_cache() in tests.
_cached_helpers = None


def _reset_helpers_cache() -> None:
    """Clear the cached helpers tuple (for test teardown)."""
    global _cached_helpers
    _cached_helpers = None


def _get_plugin_config(agent) -> dict:
    """Read plugin config, returning empty dict on any failure."""
    try:
        return _bootstrap_plugin_loader().get_plugin_config(agent)
    except Exception:
        return {}


def _get_last_user_message(agent) -> str | None:
    """Extract the last user message text from the agent.

    Returns the message string, or None if not found.
    """
    try:
        msg = getattr(agent, "last_user_message", None)
        if msg is not None:
            text = getattr(msg, "message", None)
            if text:
                return text
    except Exception:
        pass
    return None


import importlib.util
import os
import sys


def _bootstrap_plugin_loader():
    if '_plugin_loader' not in sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    return sys.modules['_plugin_loader']


def _load_module_by_path(module_name, file_path):
    return _bootstrap_plugin_loader().load_module_by_path(module_name, file_path)



def _import_helpers():
    """Lazy import of skill_match, telemetry, and phase_governance helpers.

    Uses importlib.util.spec_from_file_location to load modules by
    absolute path.  No sys.path manipulation, no _plugin_loader dependency.
    Checks sys.modules first so that test mocks (patching the standard
    module path) are respected.

    Result is cached at module level to avoid repeated _load_module_by_path
    calls on every execute().  Reset via _reset_helpers_cache().

    NOTE: We cache MODULE objects, not function references, so that test
    patches (which replace module-level attributes) remain effective.
    """
    global _cached_helpers
    if _cached_helpers is not None:
        return _cached_helpers

    import os

    this_dir = os.path.dirname(os.path.abspath(__file__))
    # extensions/python/tool_execute_before/ → plugin root is 3 levels up
    plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))

    helpers_dir = os.path.join(plugin_root, 'helpers')
    ext_dir = os.path.join(plugin_root, 'extensions', 'python', 'tool_execute_after')

    _skill_match = _load_module_by_path(
        'helpers.skill_match', os.path.join(helpers_dir, 'skill_match.py'),
    )
    _telemetry = _load_module_by_path(
        'extensions.python.tool_execute_after._05_skill_telemetry',
        os.path.join(ext_dir, '_05_skill_telemetry.py'),
    )
    _phase_gov = _load_module_by_path(
        'helpers.phase_governance', os.path.join(helpers_dir, 'phase_governance.py'),
    )
    _workflow_state = _load_module_by_path(
        'helpers.workflow_state', os.path.join(helpers_dir, 'workflow_state.py'),
    )
    _skill_contracts = _load_module_by_path(
        'helpers.skill_contracts', os.path.join(helpers_dir, 'skill_contracts.py'),
    )

    # Store modules — function lookup happens at call time so test patches work
    _cached_helpers = (
        _skill_match,
        _telemetry,
        _phase_gov,
        _workflow_state,
        _skill_contracts,
    )
    return _cached_helpers


def _get_helpers():
    """Return resolved helper functions from cached modules.

    Uses _import_helpers() to get (or retrieve cached) module objects,
    then extracts the needed functions.  Because this happens at call time
    (not cache time), test patches on module attributes remain effective.
    """
    (
        _skill_match,
        _telemetry,
        _phase_gov,
        _workflow_state,
        _skill_contracts,
    ) = _import_helpers()

    return (
        _skill_match.is_target_tool,
        _skill_match.get_loaded_skills,
        _skill_match.prefilter_match,
        _skill_match.classify_skill,
        _telemetry.log_gate_decision,
        _phase_gov.get_current_phase,
        _phase_gov.get_expected_skills,
        _phase_gov.should_suppress_correction,
        _workflow_state.append_progress_event,
        _skill_contracts.get_next_skills,
        _skill_contracts.get_skill_contract,
        _skill_contracts.get_skill_conflicts,
        _skill_contracts.get_skills_for_phase,
    )


def _append_corrective_observation(
    agent, skill_name: str, reason: str | None,
    phase_context: str | None = None,
    next_skill_hint: str | None = None,
) -> None:
    """Append an in-band corrective warning/observation to agent history.

    Uses ``agent.hist_add_message()`` to add a system (non-AI) message
    that the agent will see on its next loop iteration.  Fail-safe: any
    exception is caught and logged rather than propagating.
    """
    # M2: Sanitize classifier reason to prevent injection via newlines/length
    if reason:
        reason = reason.replace('\n', ' ').replace('\r', ' ')[:200]

    warning = (
        f"Skill enforcement gate: the skill '{skill_name}' should be "
        f"loaded before proceeding. "
    )
    if phase_context:
        warning += f"{phase_context} "
    if reason:
        warning += f"{reason} "
    if next_skill_hint:
        warning += next_skill_hint
    warning += (
        f"Load it with skills_tool(action='load', "
        f"skill_name='{skill_name}')."
    )
    try:
        agent.hist_add_message(ai=False, content=warning)
    except Exception:
        _log.debug("Failed to append corrective observation", exc_info=True)


async def _apply_phase_governance(
    agent,
    unloaded: list,
    phase_gov_enabled: bool,
    contracts_enabled: bool,
    cooldown_seconds: float,
    current_phase: str | None,
    log_fn,
    mode: str,
    tool_name: str,
    get_expected_skills_fn,
    get_skills_for_phase_fn,
    should_suppress_correction_fn,
) -> list | None:
    """Apply phase-aware governance checks to unloaded candidate skills.

    Returns the (possibly filtered) unloaded list, or None to signal
    that execute() should return early (gate decision already logged).
    """
    if not phase_gov_enabled:
        return unloaded

    if current_phase is not None:
        # Build expected skills set, enriched by contract phase
        expected = get_expected_skills_fn(current_phase)

        if contracts_enabled:
            contract_phase_skills = get_skills_for_phase_fn(current_phase)
            contract_names = {s["name"] for s in contract_phase_skills}
            expected = list(set(expected) | contract_names)

        # Find first unloaded candidate that is expected in this phase
        phase_expected_candidate = None
        for c in unloaded:
            if c.name in expected:
                phase_expected_candidate = c
                break

        if phase_expected_candidate is None:
            best = unloaded[0]
            await log_fn(
                agent=agent,
                tool_name=tool_name,
                mode=mode,
                state="unexpected_for_phase",
                candidate=best.name,
                reason=f"skill not expected in {current_phase} phase",
                phase=current_phase,
            )
            return None

        # Check correction deduplication for the expected candidate
        if should_suppress_correction_fn(
            agent, tool_name, phase_expected_candidate.name,
            cooldown_seconds=cooldown_seconds,
        ):
            await log_fn(
                agent=agent,
                tool_name=tool_name,
                mode=mode,
                state="suppressed_duplicate",
                candidate=phase_expected_candidate.name,
                reason="correction recently issued within cooldown",
                phase=current_phase,
            )
            return None

        return [phase_expected_candidate]

    else:
        # Governance enabled but phase unknown — phase-agnostic fallback
        if should_suppress_correction_fn(
            agent, tool_name, unloaded[0].name,
            cooldown_seconds=cooldown_seconds,
        ):
            await log_fn(
                agent=agent,
                tool_name=tool_name,
                mode=mode,
                state="suppressed_duplicate",
                candidate=unloaded[0].name,
                reason="correction recently issued within cooldown",
                phase=None,
            )
            return None

    return unloaded


def _build_next_skill_hint(
    unloaded: list,
    contracts_enabled: bool,
    get_next_skills_fn,
    get_skill_contract_fn,
) -> tuple[str | None, str | None]:
    """Build contract-aware next-skill recommendation.

    Returns (recommended_next, recommended_next_phase) tuple.
    """
    if not contracts_enabled or not unloaded:
        return None, None
    primary = unloaded[0]
    next_list = get_next_skills_fn(primary.name)
    if not next_list:
        return None, None
    recommended_next = next_list[0]
    rec_contract = get_skill_contract_fn(recommended_next)
    recommended_next_phase = rec_contract.get("phase") if rec_contract else None
    return recommended_next, recommended_next_phase


class SkillEnforcer(Extension):
    """Phase-aware skill enforcement gate.

    Inspects target tool calls, runs a cheap prefilter, and in observe mode
    logs would-fire decisions to telemetry. In enforce mode, runs a utility-model
    classifier and appends corrective warnings when a skill should have been loaded.

    Phase-aware governance adds:
    - Reading current workflow phase from state
    - Checking if candidate is expected in current phase
    - Suppressing wrong-phase and duplicate corrections
    - Enriching telemetry with phase context
    """

    async def execute(
        self,
        tool_args: dict | None = None,
        tool_name: str | None = None,
        **kwargs,
    ) -> None:
        try:
            (
                is_target_tool,
                get_loaded_skills,
                prefilter_match,
                classify_skill,
                log_gate_decision,
                get_current_phase,
                get_expected_skills,
                should_suppress_correction,
                append_progress_event,
                get_next_skills,
                get_skill_contract,
                get_skill_conflicts,
                get_skills_for_phase,
            ) = _get_helpers()

            # ── Gate: only target tools ────────────────────────────────
            if not tool_name:
                return

            if not is_target_tool(tool_name):
                return

            # ── Read config ────────────────────────────────────────────
            cfg = _get_plugin_config(self.agent)
            mode = cfg.get("enforcement_mode", "observe")

            # ── Phase-aware governance config ───────────────────────────
            config_bool = _bootstrap_plugin_loader().config_bool
            phase_gov_enabled = config_bool(cfg.get("phase_governance_enabled", True))
            cooldown_seconds = float(
                cfg.get("enforcement_correction_cooldown_seconds", 300)
            )

            # ── Skill contracts config (Slice 4) ───────────────────────
            contracts_enabled = config_bool(cfg.get("skill_contracts_enabled", True))

            # ── Read current phase (if governance enabled) ──────────────
            current_phase = None
            if phase_gov_enabled:
                current_phase = get_current_phase(self.agent)

            # ── Get last user message ──────────────────────────────────
            last_msg = _get_last_user_message(self.agent)

            # ── Prefilter: find candidate skills ────────────────────────
            candidates = prefilter_match(self.agent, last_msg)

            if not candidates:
                # No matching skills → log no_candidate
                await log_gate_decision(
                    agent=self.agent,
                    tool_name=tool_name,
                    mode=mode,
                    state="no_candidate",
                    candidate=None,
                    reason=None,
                    phase=current_phase,
                )
                return

            # ── Check if any candidate is already loaded ────────────────
            loaded = get_loaded_skills(self.agent)

            # Find unloaded candidates
            unloaded = [c for c in candidates if c.name not in loaded]

            if not unloaded:
                # All candidates already loaded → no correction needed
                await log_gate_decision(
                    agent=self.agent,
                    tool_name=tool_name,
                    mode=mode,
                    state="already_loaded",
                    candidate=None,
                    reason=None,
                    phase=current_phase,
                )
                return

            # ── Contract-aware conflict detection (Slice 4) ─────────────
            if contracts_enabled:
                for c in unloaded:
                    conflicts = get_skill_conflicts(c.name)
                    for conflict_name in conflicts:
                        if conflict_name in loaded:
                            _log.warning(
                                "Skill conflict detected: candidate '%s' conflicts with loaded '%s'",
                                c.name, conflict_name,
                            )

            # ── Phase-aware governance checks ──────────────────────────
            unloaded = await _apply_phase_governance(
                self.agent, unloaded,
                phase_gov_enabled, contracts_enabled, cooldown_seconds,
                current_phase, log_gate_decision, mode, tool_name,
                get_expected_skills, get_skills_for_phase,
                should_suppress_correction,
            )
            if unloaded is None:
                return

            # ── Build phase context for correction messages ─────────────
            phase_context = None
            if current_phase:
                phase_context = f"In the {current_phase} phase, this skill is expected."

            # ── Contract-aware next-skill recommendation ─────────────────
            recommended_next, recommended_next_phase = _build_next_skill_hint(
                unloaded, contracts_enabled,
                get_next_skills, get_skill_contract,
            )

            # ── Branch on mode ──────────────────────────────────────────
            if mode == "enforce":
                # Enforce mode: run classifier, possibly append corrective warning
                verdict = await classify_skill(
                    agent=self.agent,
                    tool_name=tool_name,
                    tool_args=tool_args or {},
                    candidates=unloaded,
                    last_user_message=last_msg,
                )

                state = verdict["state"]

                if state == "should_correct":
                    # Build next-skill recommendation suffix (Slice 4)
                    next_skill_hint = ""
                    if recommended_next:
                        next_skill_hint = (
                            f" After this skill, consider loading '"
                            f"{recommended_next}'"
                        )
                        if recommended_next_phase:
                            next_skill_hint += f" ({recommended_next_phase} phase)."
                        else:
                            next_skill_hint += "."

                    # Append in-band corrective observation with phase context
                    _append_corrective_observation(
                        self.agent,
                        skill_name=verdict["candidate"],
                        reason=verdict.get("reason"),
                        phase_context=phase_context,
                        next_skill_hint=next_skill_hint,
                    )

                    # Log gate_correction progress event for dedup tracking
                    append_progress_event(self.agent, {
                        "event": "gate_correction",
                        "candidate": verdict["candidate"],
                        "phase": current_phase,
                        "tool": tool_name,
                    })

                await log_gate_decision(
                    agent=self.agent,
                    tool_name=tool_name,
                    mode=mode,
                    state=state,
                    candidate=verdict.get("candidate"),
                    reason=verdict.get("reason"),
                    phase=current_phase,
                    recommended_next=recommended_next,
                )
            else:
                # Observe mode: log would-fire, do NOT call classifier,
                # do NOT mutate tool_args
                await log_gate_decision(
                    agent=self.agent,
                    tool_name=tool_name,
                    mode="observe",
                    state="should_correct",
                    candidate=unloaded[0].name,
                    reason="would-fire: skill not loaded",
                    phase=current_phase,
                    recommended_next=recommended_next,
                )

        except Exception:
            # Enforcer MUST NOT break the agent loop under any circumstances.
            _log.debug("Skill enforcer failed", exc_info=True)
