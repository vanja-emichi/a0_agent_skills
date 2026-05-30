# Spec: Phase-Aware Workflow Governance

*Phase 3 / Slice 3 of the `a0_agent_skills` workflow-governance roadmap.*
*Date: 2026-05-30*

> **Status in broader roadmap:** This document defines **Phase 3 / Slice 3** of the larger `a0_agent_skills` workflow-governance roadmap.
> The primary long-range roadmap documents are:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

## Assumptions

1. This slice lives entirely in `a0_agent_skills` (user-space plugin); no edits to `/a0/agent.py`, `models.py`, `history.py`, or any core framework module.
2. Slice 1 (Skill Enforcement Gate) is complete and stable: 389 tests passing, observe-first default, enforce mode with utility-model classifier.
3. Slice 2 (Durable Workflow State) is complete and stable: 473 total tests passing, all 7 state artifact types read/write, persist + rehydrate extensions functional.
4. The existing `current_phase.json` schema from Slice 2 is the authoritative phase-state format. Slice 3 extends it with richer transition semantics, not a new schema.
5. The existing enforcement gate (`_10_skill_enforcer.py`) is the target for phase-aware broadening — no new extension is needed for enforcement.
6. Phase-skill mapping is maintained in a dedicated helper module (`helpers/phase_governance.py`), not embedded in the enforcer body.
7. Phase transitions are advisory and self-correcting — the plugin records and suggests phase transitions but never blocks the agent loop.
8. All imports of plugin helpers from extensions continue using the `importlib` / direct-import pattern from Slice 1.
9. No hard human-intervention mode (`InterventionException`) is added in the MVP.
10. Enforcement behavior remains observe-first by default — phase-aware enforcement only activates when `enforcement_mode: enforce` is set.

## Objective

Make the enforcement gate **phase-aware** so that corrections are contextually appropriate, less repetitive, and aligned with the six-phase engineering lifecycle.

Specifically, this slice ensures:

- The plugin maintains a durable, explicit understanding of which workflow phase the agent is currently in (DEFINE, PLAN, BUILD, VERIFY, REVIEW, SHIP).
- The enforcement gate uses the current phase to select which skills are expected, rather than relying solely on keyword prefiltering.
- Prior corrections recorded in checkpoints prevent the gate from issuing repeated corrections for the same situation.
- Phase transitions are logged and validated so the plugin can detect phase-skipping or out-of-order transitions.

**Users:** (a) the maintainer running their own A0 instance; (b) the community installing the distributable plugin; (c) future agents resuming long-running project work.

**Success looks like:** the enforcement gate produces fewer false-positive corrections, respects the current workflow phase, does not repeat corrections that were already issued, and logs phase-aware telemetry that operators can use to tune phase-skill mapping.

## Tech Stack

- Python 3.11+
- Agent Zero plugin extension system (`helpers.extension.Extension`)
- Existing `helpers/workflow_state.py` (Slice 2 — phase read/write)
- Existing `helpers/skill_match.py` (Slice 1 — prefilter, classify, loaded-skill lookup)
- Existing `_10_skill_enforcer.py` (Slice 1 — the gate to broaden)
- Existing `_10_persist_workflow_state.py` (Slice 2 — persist phase transitions)
- Existing `_67_reattach_workflow_state.py` (Slice 2 — rehydrate phase state)
- Project-scoped persistence in `.a0proj/state/`
- pytest for verification

## Commands

```
Test (all):        cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ --tb=short
Test (phase):      python -m pytest tests/test_phase_governance.py -v
Test (enforcer):   python -m pytest tests/test_skill_enforcer.py -v
Parity report:     python scripts/parity_report.py
```

## Phase Model

### The Six Phases

The plugin recognizes six engineering lifecycle phases, matching the SDLC model from the plugin's routing rules:

| Phase | Description | Expected Skills
|-------|-------------|----------------
| `DEFINE` | Requirements elicitation, specification writing | `interview-me`, `spec-driven-development`
| `PLAN` | Task breakdown, implementation ordering | `planning-and-task-breakdown`, `context-engineering`
| `BUILD` | Code implementation, incremental delivery | `incremental-implementation`, `test-driven-development`, `source-driven-development`, `doubt-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`
| `VERIFY` | Testing, debugging, proving correctness | `browser-testing-with-devtools`, `debugging-and-error-recovery`
| `REVIEW` | Code review, security audit, simplification | `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization`
| `SHIP` | Deployment, CI/CD, documentation, launch | `shipping-and-launch`, `ci-cd-and-automation`, `git-workflow-and-versioning`, `documentation-and-adrs`, `deprecation-and-migration`

### Phase Transition Rules

Phases transition in forward order: DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP.

| From | To | Valid? | Notes
|------|----|--------|-------
| none | DEFINE | Yes | Initial entry
| DEFINE | PLAN | Yes | Normal forward
| PLAN | BUILD | Yes | Normal forward
| BUILD | VERIFY | Yes | Normal forward
| VERIFY | REVIEW | Yes | Normal forward
| REVIEW | SHIP | Yes | Normal forward
| any | same | Yes | Re-entry / continuation (no-op)
| any | earlier | Yes | Rewind (allowed, logged as `phase_rewind`)
| none | any non-DEFINE | Warn | Jump-start detected, logged as `phase_jump`

Phase transitions are **advisory** — they are logged and may trigger warnings, but they never block the agent loop.

### Phase-State File Extension

The existing `current_phase.json` schema from Slice 2 is extended with optional transition metadata:

```json
{
  "version": 1,
  "updated_at": 1234567890.0,
  "phase": "BUILD",
  "phases_completed": ["DEFINE", "PLAN"],
  "entered_at": 1234567890.0,
  "transition_from": "PLAN",
  "transition_type": "forward"
}
```

New optional fields:
- `transition_from` (string, optional): the previous phase
- `transition_type` (string, optional): one of `forward`, `rewind`, `reentry`, `jump`, `initial`

These fields are informational — they do not gate transitions. They enrich telemetry and the rehydrated state block.

### Phase Helper API

A new helper module `helpers/phase_governance.py` provides:

```python
def get_current_phase(agent) -> str | None
    """Return the current phase name, or None if unknown."""

def get_expected_skills(phase: str) -> list[str]
    """Return the list of skill names expected for the given phase."""

def is_phase_valid_transition(from_phase: str | None, to_phase: str) -> dict
    """Validate a phase transition. Returns:
    {
        "valid": bool,
        "transition_type": str,  # forward, rewind, reentry, jump, initial
        "warning": str | None     # non-null for rewinds and jumps
    }
    """

def transition_phase(agent, new_phase: str) -> dict | None
    """Execute a phase transition: validate, update state, log progress.
    Returns transition info dict or None on failure."""

def get_last_correction_for_context(agent, tool_name: str, candidate: str) -> dict | None
    """Check if a correction for this candidate was already issued recently.
    Uses checkpoint/progress-log state. Returns the correction record or None."""

def should_suppress_correction(agent, tool_name: str, candidate: str, cooldown_seconds: float = 300.0) -> bool
    """Return True if a recent correction for this candidate/context was already issued.
    Prevents correction loops."""
```

## Phase-Aware Enforcement

### How the Enforcer Becomes Phase-Aware

The existing `_10_skill_enforcer.py` is extended to:

1. **Read the current phase** from workflow state before deciding whether to correct.
2. **Use phase-skill mapping** to determine if the candidate skill is expected in the current phase.
3. **Check prior corrections** to avoid repeating the same correction within a cooldown window.
4. **Log phase-aware telemetry** so operators can measure phase-skill alignment.

### Enforcement Decision Flow (Phase-Aware)

```
Target tool call detected
  │
  ├── Prefilter: find candidate skills (unchanged)
  │
  ├── Check loaded skills (unchanged)
  │
  ├── NEW: Read current phase from state
  │       │
  │       ├── Phase known?
  │       │     ├── Yes: Get expected skills for this phase
  │       │     │       │
  │       │     │       ├── Candidate is expected in this phase?
  │       │     │       │     ├── Yes: proceed with normal correction logic
  │       │     │       │     └── No: log `unexpected_for_phase`, skip correction
  │       │     │       │
  │       │     │       └── Check prior correction (cooldown)
  │       │     │             ├── Already corrected recently? → skip, log `suppressed_duplicate`
  │       │     │             └── Not corrected recently → proceed with correction
  │       │     │
  │       │     └── No phase known: proceed with phase-agnostic logic (backward compat)
  │       │
  │       └── Enforce mode: run classifier (unchanged)
  │       ┌─ Observe mode: log would-fire (enriched with phase info)
  │       └─ Enforce mode: append corrective warning (enriched with phase context)
```

### Phase Context in Corrections

When a correction is issued in enforce mode, the warning message includes phase context:

```
Skill enforcement gate: the skill 'test-driven-development' should be
loaded before proceeding. In the BUILD phase, this skill is expected.
Load it with skills_tool(action='load', skill_name='test-driven-development').
```

When a correction is suppressed because the candidate is not expected in the current phase:

```
Phase-aware suppression: skill 'shipping-and-launch' is not expected in
the current BUILD phase. Logging but not correcting.
```

### Checkpoint-Aware Deduplication

The enforcer checks the progress log for recent correction events before issuing a new correction. This prevents correction loops where the same candidate is flagged repeatedly.

**Cooldown logic:**
- After a correction is issued for candidate `X`, it is logged to the progress log as a `gate_correction` event.
- Before issuing a new correction for the same candidate, the enforcer checks if a `gate_correction` event for that candidate was logged within the last `enforcement_correction_cooldown_seconds` (default 300 seconds / 5 minutes).
- If a recent correction exists, the new correction is suppressed and logged as `suppressed_duplicate`.

**Progress log event shape for corrections:**

```jsonl
{"ts":1234567890.0,"event":"gate_correction","candidate":"test-driven-development","phase":"BUILD","tool":"code_execution_tool"}
```

**Event type:** `gate_correction` (new — not in the original Slice 2 event type list, but added as a valid `custom`-adjacent event).

### Config Surface

New config keys in `default_config.yaml`:

```yaml
# Phase-aware governance — extends enforcement with phase context
phase_governance_enabled: true                    # Set to false to disable phase-aware enforcement
enforcement_correction_cooldown_seconds: 300      # Minimum seconds between corrections for the same candidate
```

## Integration Points

### With Slice 1 (Enforcement Gate)

- The enforcer gains two new imports from `helpers/phase_governance`: `get_current_phase`, `get_expected_skills`, `should_suppress_correction`.
- The existing enforcement flow is preserved — phase-awareness is additive, not replacing.
- When `phase_governance_enabled: false`, the enforcer behaves exactly as before.
- The classifier prompt is optionally enriched with phase context ("The agent is in the BUILD phase").

### With Slice 2 (Durable Workflow State)

- Phase state continues to be stored in `current_phase.json` via `workflow_state.save_current_phase`.
- Phase transitions are logged to `progress_log.jsonl` via `workflow_state.append_progress_event`.
- The rehydrate extension already restores phase state — no changes needed there.
- The persist extension already saves phase changes — no changes needed there.

### New Files

```text
helpers/phase_governance.py           ← NEW: phase helper, phase-skill mapping, transition logic, correction dedup
```

### Modified Files

```text
extensions/python/tool_execute_before/_10_skill_enforcer.py   ← EXTEND: phase-aware decision flow
default_config.yaml                                            ← EXTEND: phase_governance_enabled, correction cooldown
```

### New Test Files

```text
tests/test_phase_governance.py          ← NEW: unit + behavioral tests for phase helper
tests/test_skill_enforcer.py            ← EXTEND: phase-aware enforcement tests
```

## Testing Strategy

### Unit Tests (helpers/phase_governance.py)

- `get_expected_skills` returns correct skill lists for all 6 phases
- `is_phase_valid_transition` correctly identifies forward, rewind, reentry, jump, initial transitions
- `get_current_phase` returns None when no state exists
- `get_current_phase` returns the stored phase when state exists
- `transition_phase` updates state and logs progress event
- `transition_phase` handles invalid phase names gracefully
- `should_suppress_correction` returns False when no prior corrections exist
- `should_suppress_correction` returns True when a recent correction exists within cooldown
- `should_suppress_correction` returns False when prior correction is outside cooldown window

### Behavioral Tests (enforcer integration)

- In DEFINE phase, enforcer flags missing `spec-driven-development` as expected
- In BUILD phase, enforcer flags missing `test-driven-development` as expected
- In BUILD phase, enforcer does NOT flag missing `shipping-and-launch` (wrong phase)
- In SHIP phase, enforcer flags missing `shipping-and-launch` as expected
- When phase is unknown, enforcer falls back to phase-agnostic behavior (backward compat)
- When `phase_governance_enabled: false`, enforcer behaves exactly as Slice 1
- Repeated correction for same candidate within cooldown is suppressed
- Correction after cooldown expires is allowed
- Phase-aware telemetry includes phase field in decision records

### Regression Tests

- All existing Slice 1 tests pass unchanged
- All existing Slice 2 tests pass unchanged
- Full suite: 473+ tests green

## Boundaries

### Always

- Keep phase transitions advisory — never block the agent loop
- Default `phase_governance_enabled: true` — phase-aware logic is opt-out, not opt-in
- Keep enforcement observe-first when `enforcement_mode: observe`
- Wrap all new logic in fail-safe try/except
- Log phase-aware decisions to existing telemetry infrastructure
- Use existing `workflow_state` helper for all state I/O — no direct file access

### Ask First

- Adding new target tools to the enforcement gate
- Changing the phase-skill mapping (it should be configurable in a future slice)
- Adding hard human-intervention mode
- Expanding the cooldown mechanism beyond simple time-based dedup

### Never

- Edit core framework files
- Use `nudge()` as the correction primitive
- Force tool rewrites in MVP
- Block agent execution on phase validation failures
- Introduce new external dependencies

## Success Criteria (testable)

1. The phase helper returns correct expected-skill lists for all 6 phases (asserted).
2. Phase transitions are validated and logged: forward transitions produce no warning, rewinds/jumps produce `phase_rewind`/`phase_jump` log entries.
3. In enforce mode, the enforcer considers the current phase when deciding whether to correct — corrections are suppressed for skills not expected in the current phase.
4. In observe mode, the enforcer logs phase-aware would-fire decisions including the current phase, but does NOT call the classifier or mutate tool_args.
5. Correction deduplication works: a second correction for the same candidate within the cooldown window is suppressed and logged as `suppressed_duplicate`.
6. Correction deduplication respects cooldown: after cooldown expires, the correction is allowed again.
7. When phase state is unknown, the enforcer falls back to phase-agnostic behavior identical to Slice 1.
8. When `phase_governance_enabled: false`, the enforcer behaves exactly as Slice 1 — zero behavioral change.
9. All existing 473 tests remain green — no regressions.
10. Phase-aware telemetry records include a `phase` field when phase is known.

## Open Questions

1. Should the phase-skill mapping be configurable via YAML instead of hardcoded in the helper? (Deferred to a future slice — MVP uses a hardcoded mapping.)
2. Should the cooldown window be per-candidate or global? (MVP: per-candidate — each candidate has its own cooldown.)
3. Should the enforcer suggest phase transitions (e.g., "you're in DEFINE but about to write code — consider transitioning to BUILD")? (Deferred — the rehydrate extension already shows the current phase; explicit transition suggestions are a future enhancement.)
4. Should `gate_correction` be a first-class event type in `_VALID_EVENT_TYPES`, or should it use the `custom` event type? (MVP: added as a first-class type — it has structured fields that `custom` doesn't guarantee.)
