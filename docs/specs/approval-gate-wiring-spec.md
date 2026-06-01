# Spec: Approval Gate Wiring and Governance Hardening

**Status:** Shipped
**Parent:** `docs/specs/a0-agent-skills-workflow-governance-spec.md`
**Related ADRs:** ADR-001 (Skill Enforcement Gate), ADR-002 (Durable Workflow State), ADR-003 (Phase-Aware Governance), ADR-006 (Enforcement Strict Mode)

## Objective

Wire the existing approval infrastructure (`mark_artifact_approved`, `is_artifact_approved`, `approval` event type) to a natural language trigger, then incrementally harden the governance system with test gates at every step. The 5 code bugs from the deep analysis are already fixed; this spec covers the remaining wiring and hardening work.

### Problem Statement

1. **Dead code:** `mark_artifact_approved` and `is_artifact_approved` exist in `helpers/workflow_state.py`, have 6+ passing tests, and are referenced in rehydration display logic — but no production code calls them. Artifacts never get approved in practice.
2. **Behavioral layer is weak:** Bug 8 (skipped VERIFY phase) occurred with all enforcement settings enabled, proving the gate cannot catch behavioral violations. The routing rules need explicit approval gate semantics.
3. **Classifier accuracy is 40.6%:** Shadow sampling is off (`enforcement_shadow_sample_rate: 0`), so we have no data to improve the classifier.

### Success Looks Like

- 4 mandatory approval gates (G1: DEFINE→PLAN, G2: PLAN→BUILD, G3: BUILD→REVIEW→SHIP, G4: REVIEW→SHIP) detect natural language approval and block phase transitions when unapproved
- Classifier accuracy ≥ 80% on the existing eval fixtures
- Enforce mode enabled and verified in a live session
- Zero regressions in the 839 existing tests

## Commands

```bash
# Plugin tests
cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ -v --tb=short

# Eval suite
cd /a0/usr/plugins/a0_agent_skills && python tests/run_enforcement_evals.py

# Specific test files
cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/test_workflow_state.py tests/test_persist_workflow_state.py tests/test_phase_governance.py -v --tb=short

# Linting (if configured)
cd /a0/usr/plugins/a0_agent_skills && python -m py_compile helpers/*.py extensions/python/**/*.py
```

## Project Structure

Files to create or modify:

```
/a0/usr/plugins/a0_agent_skills/
├── helpers/
│   └── workflow_state.py           # Extend mark_artifact_approved with mtime tracking
├── extensions/python/
│   ├── tool_execute_before/
│   │   └── _20_approval_gate.py     # NEW: natural language detection + phase gate check
│   └── tool_execute_after/
│       └── _10_persist_workflow_state.py  # No changes (already correct)
├── tests/
│   ├── test_approval_trigger.py    # NEW: natural language detection tests
│   ├── test_approval_phase_gate.py  # NEW: phase gate enforcement tests
│   ├── test_approval_mtime.py       # NEW: mtime invalidation tests
│   └── test_workflow_state.py       # EXTEND: mtime tracking tests
├── prompts/
│   └── agent.skills.routing.md     # UPDATE: add 4 mandatory gates to routing rules
├── config.json                      # UPDATE: shadow_sample_rate, later enforcement_mode
└── default_config.yaml              # No changes (defaults already correct)
```

## Code Style

- Follow existing patterns: fail-safe defaults, `_log.warning` for non-critical errors
- New extension: `_NN_descriptive_name.py` naming convention with bootstrap pattern
- Approval detection: case-insensitive phrase matching with word boundaries
- All new functions return safe defaults on exception (never crash the agent loop)
- Match the existing `mark_artifact_approved` signature: `(agent, artifact_type) -> str | None`

### Example: Approval detection function

```python
_APPROVAL_PHRASES = frozenset([
    "approved", "approve", "looks good", "good to go",
    "proceed", "ship it", "lgtm", "let's go",
])

def detect_approval_in_text(text: str) -> bool:
    """Detect explicit approval language in user text.

    Returns True only for explicit positive signals. Does NOT treat
    silence, questions, or feedback as approval.
    """
    if not text:
        return False
    text_lower = text.lower()
    # Word-boundary matching to avoid false positives like "unapproved"
    for phrase in _APPROVAL_PHRASES:
        if re.search(rf'\b{re.escape(phrase)}\b', text_lower):
            return True
    return False
```

## Testing Strategy

| Level | Framework | Location | Coverage Target |
|-------|-----------|----------|-----------------|
| Unit | pytest | `tests/test_approval_*.py` | All new functions, edge cases, mtime invalidation |
| Integration | pytest | `tests/test_workflow_state.py` | Approval + state persistence |
| Eval | custom runner | `tests/run_enforcement_evals.py` | Classifier accuracy ≥ 80% |
| Live | manual | N/A | Full spec→plan→build cycle with gates |

### Test Cases Required

1. **Approval trigger (positive):** "approved", "looks good", "proceed", "ship it" → `mark_artifact_approved` called
2. **Approval trigger (negative):** "fix section 3", "unapproved", "approved by whom?" → no approval triggered
3. **Phase gate (blocked):** try DEFINE→PLAN without approved spec → transition blocked, warning logged
4. **Phase gate (allowed):** approve spec, then DEFINE→PLAN → transition succeeds
5. **Mtime invalidation:** approve spec → modify spec → approval is invalid, gate blocks again
6. **Classifier accuracy:** eval suite with `enforcement_shadow_sample_rate: 0.1` → accuracy ≥ 80%
7. **Enforce mode live test:** in a session, agent receives corrections for skill skips

## Boundaries

### Always Do

- Run `python -m pytest tests/ -v --tb=short` after every code change
- Keep `enforcement_mode: "observe"` until Steps 1-5 pass
- Read the relevant AGENTS.md before editing any file
- Follow the closeout protocol after each step
- Document any deviations from this spec in `docs/reports/`

### Ask First

- Changing `enforcement_mode` from `observe` to `enforce` (only after explicit user approval)
- Adding new dependencies
- Modifying the routing rules template structure
- Changing the phase model or transition logic

### Never Do

- Skip test gates between steps
- Enable `enforce` mode without shadow sample data showing ≥80% accuracy
- Remove or weaken existing tests
- Hardcode paths in new code (use `workflow_state` helpers)
- Bypass the fail-safe error handling pattern
- Re-propose work covered by already-shipped specs

## Success Criteria

### Step Gates (each independently verifiable)

- [ ] **Step 1:** Approval trigger detects natural language; 6+ unit tests pass; full suite green
- [ ] **Step 2:** Phase gate blocks unapproved transitions; unit tests for blocked/allowed/mtime cases; full suite green
- [ ] **Step 3:** Mtime invalidation works; unit tests pass; full suite green
- [ ] **Step 4:** Shadow sampling enabled; classifier is being called; no behavioral change
- [ ] **Step 5:** Classifier accuracy ≥ 80% on eval suite
- [ ] **Step 6:** Enforce mode enabled; live test shows corrections being injected; no false positives
- [ ] **Step 7:** Routing rules updated with 4 mandatory gates; existing routing tests still pass
- [ ] **Step 8:** Full E2E session: spec → approval → plan → approval → build; all gates trigger correctly

### Final Outcome Criteria

- [ ] All 4 approval gates (G1-G4) trigger in a live session at the correct phase transitions
- [ ] Telemetry shows `approval` events with correct artifact types and timestamps
- [ ] Rehydration displays `(approved)` tags next to approved artifacts
- [ ] Mtime invalidation works: modifying an approved artifact re-blocks phase transition
- [ ] Zero regressions in the existing 839 tests
- [ ] Classifier accuracy ≥ 80% on eval fixtures
- [ ] Enforce mode is safe to run (no false positive corrections in normal skill usage)

## Out of Scope

- Framework-level changes (Agent Zero `tool_execute_before` return value handling is a framework constraint we cannot change)
- New skills, agents, or commands
- Routing rules beyond the 4 approval gates
- Behavioral compliance mechanisms beyond approval gates (e.g., phase skipping detection)
- Multi-language approval detection (English only for v1)
- Auto-approval mechanisms
- Approval expiry or budget controls
- Approval delegation to other agents

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| False positive corrections in enforce mode | Stay in observe until eval accuracy ≥ 80%; use shadow sampling first |
| Natural language detection is too aggressive | Start with a tight phrase list; add word-boundary matching to avoid "unapproved" matching |
| Natural language detection is too narrow | Track false negatives in telemetry; iterate the phrase list based on real user patterns |
| Mtime invalidation breaks legitimate workflows | Only invalidate on actual file write events, not reads |
| Phase gate causes infinite loops | The agent is already designed to loop in the current phase; this is expected behavior |

## Open Questions

None at this time. The spec is self-contained. Any discoveries during implementation should be documented in `docs/reports/` and the spec updated accordingly.

## Related Context

- Spec: `docs/specs/enforcement-settings-verification-spec.md` (Shipped — sibling work)
- Plan: `docs/plans/enforcement-settings-verification-plan.md` (Shipped)
- Report: `docs/reports/skill-checkpoint-gate-analysis.md` (4 mandatory gates analysis)
- ADR-006: Enforcement strict mode decision (framework constraint)
- Plugin AGENTS.md: `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
- Project AGENTS.md: `/a0/usr/projects/a0_agent_skills/AGENTS.md`
