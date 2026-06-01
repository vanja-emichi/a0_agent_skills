# ADR-009: Approval Gate System — From Dead Code to Enforced Lifecycle Gates

**Date**: 2026-06-02
**Status**: Accepted
**Supersedes**: Enhances ADR-006 (enforcement strict mode)

## Context

The plugin had approval infrastructure (`mark_artifact_approved`, `is_artifact_approved` in `workflow_state.py`) but it was dead code — these functions were never called anywhere in the codebase. Analysis of all 23 skills' checkpoint phrases revealed 4 mandatory approval gates that were documented but unenforced:

| Gate | Transition | Blocks Until |
|------|-----------|-------------|
| G1 | DEFINE → PLAN | User approves spec |
| G2 | PLAN → BUILD | User approves plan |
| G3 | BUILD → REVIEW → SHIP | Code review passes with no criticals |
| G4 | REVIEW → SHIPPED | User approves + all checklist items done |

Additionally, the enforcement classifier (ADR-006) had only 40.6% accuracy, enforcement was advisory-only (`observe` mode), and no mechanism existed to invalidate approvals when artifacts changed after approval.

## Decision

### 1. Wire Existing Approval Infrastructure to Natural Language Detection

Create `_20_approval_gate.py` extension that:
- Detects approval phrases ("approved", "looks good", "proceed", "ship it", etc.) using word-boundary regex matching
- Rejects negations ("not approved", "don't proceed") and questions ("approved?") with explicit pattern exclusion
- Calls `mark_artifact_approved` on positive detection with the current artifact path

### 2. Phase Gate Check Before Transitions

Add `check_phase_approval_gate(phase)` in helpers:
- In `enforce` mode: returns `False` (blocks transition) if artifact not approved
- In `observe` mode: logs warning but returns `True` (allows transition)
- Checks only apply to forward phase transitions; backward transitions (revisions) are always allowed

### 3. Mtime Invalidation for Artifact Changes

Extend `mark_artifact_approved` to store file modification time alongside approval:
```python
"approval": {
    "approved": True,
    "mtime": os.path.getmtime(artifact_path)
}
```

`is_artifact_approved` checks stored mtime against current file mtime. If the file was modified after approval, the approval is invalidated (returns `False`).

### 4. Shadow Sampling for Data Collection

At 10% sample rate in observe mode, invoke the skill classifier on tool calls to collect accuracy data without affecting behavior. This provides ongoing metrics for classifier improvement.

### 5. Classifier Tuning

Improved prompt patterns in `skill_match.py` to achieve 93.6% accuracy (88/94 fixtures), up from 40.6%:
- Better skill description matching
- Reduced false positives on partial keyword matches
- Explicit handling of ambiguous tool calls

### 6. Enable Enforce Mode

Switch `config.json` enforcement mode from `observe` to `enforce`:
- Corrections are actively injected when skills are skipped
- No false positives on skill-loaded calls (classifier distinguishes loaded vs. needed)
- Fail-safe design: `enforce` mode returns `False` on errors (deny by default), `observe` mode returns `True`

### 7. Strengthen Routing Rules

Update `agent.skills.routing.md` with:
- 4 mandatory approval gates (G1–G4) with explicit blocking behavior
- Anti-rationalization table preventing common bypass justifications
- Persona invocation rules for code-reviewer, security-auditor, test-engineer
- Approval gate table at the top level of the injected system prompt

### 8. Fail-Safe Design Principle

Enforcement follows deny-by-default:
- `enforce` mode errors → return `False` (block transition)
- `observe` mode errors → return `True` (allow transition, log warning)
- Classifier uncertain → treat as skill needed (enforce loading)
- Approval state corrupted → treat as not approved

## Alternatives Considered

### Alternative A: Build approval into each skill individually
- **Pros:** Fine-grained control per skill, skills own their approval logic
- **Cons:** 23 skills to modify, inconsistent enforcement, hard to audit
- **Rejected:** Centralized enforcement is more reliable and auditable

### Alternative B: Use a separate approval service/daemon
- **Pros:** Language-agnostic, could serve multiple agents
- **Cons:** Adds infrastructure dependency, latency, failure mode outside agent
- **Rejected:** In-process enforcement is simpler and more reliable

### Alternative C: String-only approval (no mtime check)
- **Pros:** Simpler implementation, no file system dependency
- **Cons:** Approval survives artifact changes — user approves v1, agent ships v2
- **Rejected:** Mtime check is essential for approval integrity

### Alternative D: Gradual rollout (observe mode permanently)
- **Pros:** No risk of false blocks, data collection phase
- **Cons:** Approval gates remain advisory, original bugs persist
- **Rejected:** 93.6% classifier accuracy is sufficient for enforcement; shadow sampling continues for monitoring

## Consequences

- **Agent now requires explicit user approval before advancing lifecycle phases** — the 4 gates (G1–G4) are actively enforced
- **Approval is invalidated if the artifact changes after approval** — mtime tracking ensures approval matches the current artifact
- **Enforcement actively injects corrections when skills are skipped** — no more silent bypass of mandatory skills
- **Fail-safe by default** — errors in enforcement mode deny transitions rather than allow them
- **Ongoing accuracy monitoring** — shadow sampling continues at 10% rate even in enforce mode
- **981 tests passing, 0 failures** — comprehensive test coverage including 40 acceptance integration tests

## Follow-Up Items

| ID | Item | Status |
|----|------|--------|
| I-1 | Deduplicate approval phrase map across modules | Fixed |
| I-2 | Handle questions with approval words ("should I approve?") | Fixed |
| M-1 | Fail-open on errors in observe mode | Fixed |
| M-2 | Negation detection window (multi-word negations) | Fixed |
| M-3 | Unknown message types in classifier | Fixed |
| — | Monitor classifier accuracy in production via shadow sampling | Ongoing |
| — | Consider raising shadow sample rate if accuracy drifts below 90% | Ongoing |
