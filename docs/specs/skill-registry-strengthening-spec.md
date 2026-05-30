# Spec: Skill Registry Strengthening

*Phase 4 / Slice 4 (final) of the `a0_agent_skills` workflow-governance roadmap.*
*Date: 2026-05-30*

> **Status in broader roadmap:** This document defines **Phase 4 / Slice 4** of the larger `a0_agent_skills` workflow-governance roadmap.
> The primary long-range roadmap documents are:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

## Assumptions

1. This slice lives entirely in `a0_agent_skills` (user-space plugin); no edits to `/a0/agent.py`, `models.py`, `history.py`, or any core framework module.
2. Slices 1–3 are complete and stable: 550 tests passing, enforcement gate functional, durable workflow state operational, phase-aware governance active.
3. The existing `PHASE_SKILL_MAP` in `helpers/phase_governance.py` is the authoritative phase-skill mapping. Slice 4 enriches it with contract metadata read from skill files, not a replacement.
4. SKILL.md files already contain YAML frontmatter with `name`, `version`, `description`, `tags`, and `trigger_patterns`. Slice 4 adds optional contract fields to this existing frontmatter block — no new file format.
5. Skills without contract fields continue to load and function identically. Backward compatibility is absolute.
6. The dependency graph is derived from contract metadata at runtime — not hardcoded. This means the graph is always consistent with whatever skills are installed.
7. No circular dependencies are allowed among the core lifecycle skills (DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP).
8. All imports of plugin helpers from extensions continue using the `importlib` / direct-import pattern from Slice 1.
9. No new external dependencies are introduced.

## Objective

Strengthen the skill registry so that core engineering skills carry **rich, machine-readable contracts** and the plugin can navigate **explicit dependency / next-skill relationships** across the six-phase lifecycle.

Specifically, this slice ensures:

- Each core engineering skill can declare a **contract** in its SKILL.md frontmatter: expected inputs, produced artifacts, verification steps, next-skill recommendations, phase assignment, and conflict declarations.
- The plugin can **parse contracts** from all installed skills and build a **dependency graph** from them at runtime.
- The phase-aware enforcer uses contract data for **better matching** — it knows what a skill expects and produces, not just which phase it belongs to.
- The plugin can **recommend the next skill** in the workflow lifecycle, surfaced through telemetry and rehydration prompts.
- Skills without contracts load and behave exactly as before — zero breakage.

**Users:** (a) the maintainer running their own A0 instance; (b) the community installing the distributable plugin; (c) future agents resuming long-running project work.

**Success looks like:** every core lifecycle skill has a contract, the dependency graph is queryable, the enforcer makes smarter phase-aware decisions using contract metadata, and next-skill guidance appears in telemetry and rehydrated state.

## Tech Stack

- Python 3.11+
- Agent Zero plugin extension system (`helpers.extension.Extension`)
- Existing `helpers/workflow_state.py` (Slice 2 — state persistence)
- Existing `helpers/phase_governance.py` (Slice 3 — phase model, phase-skill mapping)
- Existing `helpers/skill_match.py` (Slice 1 — prefilter, classify, loaded-skill lookup)
- Existing `helpers/skills.py` (framework — skill loading, search)
- YAML frontmatter in SKILL.md files (no new file format)
- Project-scoped persistence in `.a0proj/state/`
- pytest for verification

## Commands

```
Test (all):          cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ --tb=short
Test (contracts):    python -m pytest tests/test_skill_contracts.py -v
Test (graph):        python -m pytest tests/test_skill_graph.py -v
Test (enforcer):     python -m pytest tests/test_skill_enforcer.py -v
Parity report:       python scripts/parity_report.py
```

## Skill Contract Format

### Location

Contract metadata lives inside the existing YAML frontmatter block of each `SKILL.md` file. This keeps contract data co-located with skill instructions and requires no new file format.

### Contract Fields

All contract fields are **optional**. A skill with no contract fields loads and functions identically to pre-Slice-4 behavior.

```yaml
---
name: spec-driven-development
version: 1.0.0
# ... existing fields ...

# ── Contract fields (Slice 4) ──
contract:
  phase: DEFINE
  inputs:
    - User request or task description
    - Existing context about the project or feature
  artifacts:
    - path: docs/specs/*.md
      description: Structured specification document
  verification:
    - Spec document exists at expected path
    - Spec contains required sections (assumptions, scope, success criteria)
    - Spec has been reviewed or acknowledged
  next_skills:
    - planning-and-task-breakdown
  conflicts: []
---
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contract.phase` | string | No | The SDLC phase this skill primarily belongs to. Must match one of `DEFINE`, `PLAN`, `BUILD`, `VERIFY`, `REVIEW`, `SHIP`. If absent, the skill is not phase-bound. |
| `contract.inputs` | list of strings | No | What the skill expects to be available or provided before it runs. Informational — not enforced. |
| `contract.artifacts` | list of objects | No | What the skill produces. Each entry has `path` (glob pattern) and `description` (string). |
| `contract.verification` | list of strings | No | Steps or checks to confirm the skill ran successfully. Informational — used for telemetry and guidance. |
| `contract.next_skills` | list of strings | No | Skill names that are logical next steps after this skill completes. Used to build the dependency graph and provide next-skill guidance. Must reference existing skill names. |
| `contract.conflicts` | list of strings | No | Skill names that should NOT be active at the same time. Used for conflict detection. |

### Backward Compatibility Rules

1. **No contract block** → skill loads normally, no contract data available.
2. **Partial contract** (e.g., only `phase` and `next_skills`) → only provided fields are parsed; missing fields default to empty.
3. **Unknown fields** in the contract block → ignored silently (forward-compatible).
4. **Invalid `phase` value** → `phase` is treated as absent; logged as a warning during parsing.
5. **Invalid `next_skills` entry** (references non-existent skill) → that entry is skipped; logged as a warning.
6. **Malformed YAML** → entire contract block is treated as absent; the skill loads normally.

## Dependency Graph

### Data Structure

The dependency graph is a directed acyclic graph (DAG) built from the `next_skills` contract fields of all installed skills. It is constructed at runtime when first queried and cached for the session.

```python
# Internal representation
graph: dict[str, dict] = {
    "spec-driven-development": {
        "phase": "DEFINE",
        "next_skills": ["planning-and-task-breakdown"],
        "conflicts": [],
    },
    "planning-and-task-breakdown": {
        "phase": "PLAN",
        "next_skills": ["incremental-implementation", "test-driven-development"],
        "conflicts": [],
    },
    # ... etc.
}
```

### Graph Construction

1. Scan all installed skill directories for `SKILL.md` files.
2. Parse YAML frontmatter from each file.
3. Extract `contract` block if present.
4. Validate: `phase` must be a known phase, `next_skills` must reference existing skills, `conflicts` must reference existing skills.
5. Store validated entries in the graph dict.
6. Check for cycles among core lifecycle skills (DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP chain). Log warnings for any cycles found.
7. Cache the result.

### Graph Queries

The graph supports these queries:

```python
def get_skill_contract(skill_name: str) -> dict | None
    """Return the parsed contract for a skill, or None if no contract exists."""

def get_next_skills(skill_name: str) -> list[str]
    """Return the list of recommended next skills after this one."""

def get_skill_conflicts(skill_name: str) -> list[str]
    """Return skills that conflict with this one."""

def get_skills_for_phase(phase: str) -> list[dict]
    """Return all contract-bearing skills for a given phase, with their contract data."""

def get_lifecycle_chain() -> list[str]
    """Return the recommended skill chain through all six phases."""

def validate_graph() -> list[dict]
    """Validate the graph for cycles, broken references, and orphan skills.
    Returns a list of validation findings."""
```

### No Circular Dependencies

The core lifecycle chain must be acyclic. After graph construction, the plugin checks that following `next_skills` from any DEFINE-phase skill never leads back to itself. If a cycle is detected:

1. A warning is logged with the cycle path.
2. The cycle edge is removed from the in-memory graph.
3. The cycle is reported in `validate_graph()` output.

## Contract-Aware Enforcement

### How Contracts Improve Enforcement

The phase-aware enforcer (Slice 3) already checks whether a candidate skill is expected in the current phase using `PHASE_SKILL_MAP`. Slice 4 enriches this:

1. **Contract phase vs. map phase**: If a skill has a `contract.phase` that differs from its assignment in `PHASE_SKILL_MAP`, the contract wins. This allows skills to declare their own phase without modifying the hardcoded map.
2. **Artifact awareness**: If the enforcer detects that a prior skill's artifacts exist (e.g., a spec file was written), it can infer that the DEFINE phase has been completed and recommend transitioning to PLAN.
3. **Next-skill suggestions**: When the enforcer issues a correction, it can include the recommended next skill in the warning message, guiding the agent through the lifecycle.
4. **Conflict detection**: If a loaded skill conflicts with a candidate skill, the enforcer can warn about the conflict rather than blindly suggesting both.

### Enhanced Correction Message

```
Skill enforcement gate: the skill 'test-driven-development' should be
loaded before proceeding. In the BUILD phase, this skill is expected.
After this skill, consider loading 'debugging-and-error-recovery' (VERIFY phase).
Load it with skills_tool(action='load', skill_name='test-driven-development').
```

### Artifact-Based Phase Inference

When the enforcer runs and the current phase is unknown or ambiguous, it can check for the existence of artifacts declared in skill contracts:

- If a spec file exists (artifact of `spec-driven-development`) → DEFINE phase is likely complete.
- If a plan file exists (artifact of `planning-and-task-breakdown`) → PLAN phase is likely complete.

This is **advisory only** — it informs the enforcement decision but does not override explicit phase state.

## Next-Skill Guidance

### How Guidance Is Surfaced

Next-skill guidance appears in three places:

1. **Telemetry**: `gate_decision` events include a `recommended_next` field when the corrected skill has a `next_skills` contract entry.

2. **Rehydration**: The `_67_reattach_workflow_state.py` extension (Slice 2) includes next-skill recommendations in the rehydrated state block when the current phase has a contract-bearing skill loaded.

3. **Correction message**: As shown above, the enforcement warning includes the next recommended skill.

### Telemetry Event Extension

```jsonl
{"ts":1234567890.0,"event":"gate_decision","tool":"code_execution_tool","candidate":"test-driven-development","phase":"BUILD","recommended_next":["debugging-and-error-recovery"],"decision":"corrected"}
```

New optional field: `recommended_next` (list of skill names).

### Rehydration State Extension

The rehydrated state block (appended to the system prompt by `_67_reattach_workflow_state.py`) gains an optional `next_skill_hints` section:

```
[Workflow State Reattached]
Current phase: BUILD
Loaded skills: test-driven-development
Phase-aware enforcement: active

Next skill hints:
- After test-driven-development: consider loading debugging-and-error-recovery (VERIFY phase)
```

## Config Surface

New config keys in `default_config.yaml`:

```yaml
# Skill registry strengthening — contracts and dependency graph
skill_contracts_enabled: true          # Set to false to disable contract parsing and graph building
skill_graph_validate_on_build: true    # Validate graph for cycles on construction
skill_next_skill_hints: true           # Include next-skill hints in rehydration and telemetry
```

## Integration Points

### With Slice 1 (Enforcement Gate)

- The enforcer reads contract data via the new `helpers/skill_contracts.py` helper.
- Contract-aware enforcement is additive — when `skill_contracts_enabled: false`, the enforcer behaves exactly as Slice 3.
- Next-skill recommendations appear in correction messages and telemetry.

### With Slice 2 (Durable Workflow State)

- Contract data is not persisted — it is always read from SKILL.md files at runtime.
- The rehydration extension reads the graph to include next-skill hints.
- No new state files are needed.

### With Slice 3 (Phase-Aware Governance)

- Contract `phase` values are cross-referenced with `PHASE_SKILL_MAP`.
- If a skill declares a contract phase that differs from the map, the contract phase takes precedence.
- The dependency graph augments phase-skill mapping with explicit ordering.

### New Files

```text
helpers/skill_contracts.py             ← NEW: contract parsing, graph building, graph queries
```

### Modified Files

```text
extensions/python/tool_execute_before/_10_skill_enforcer.py   ← EXTEND: contract-aware decision flow
extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py  ← EXTEND: next-skill hints
default_config.yaml                                            ← EXTEND: skill_contracts_enabled, skill_graph_validate_on_build, skill_next_skill_hints
skills/*/SKILL.md                                               ← EXTEND: add contract blocks to core lifecycle skills
```

### New Test Files

```text
tests/test_skill_contracts.py          ← NEW: unit tests for contract parsing
tests/test_skill_graph.py              ← NEW: unit tests for graph building and queries
```

### Skills Receiving Contracts (MVP)

The following 12 core lifecycle skills receive contract blocks in this slice:

| Skill | Phase | Next Skills |
|-------|-------|-------------|
| `interview-me` | DEFINE | `spec-driven-development` |
| `spec-driven-development` | DEFINE | `planning-and-task-breakdown` |
| `planning-and-task-breakdown` | PLAN | `incremental-implementation`, `test-driven-development` |
| `context-engineering` | PLAN | `incremental-implementation` |
| `incremental-implementation` | BUILD | `test-driven-development`, `debugging-and-error-recovery` |
| `test-driven-development` | BUILD | `debugging-and-error-recovery` |
| `source-driven-development` | BUILD | `test-driven-development` |
| `doubt-driven-development` | BUILD | `test-driven-development` |
| `debugging-and-error-recovery` | VERIFY | `code-review-and-quality` |
| `browser-testing-with-devtools` | VERIFY | `code-review-and-quality` |
| `code-review-and-quality` | REVIEW | `shipping-and-launch` |
| `shipping-and-launch` | SHIP | (none — terminal) |

The remaining 11 skills (e.g., `code-simplification`, `security-and-hardening`, `performance-optimization`, `ci-cd-and-automation`, etc.) do not receive contracts in the MVP. They continue to function normally via `PHASE_SKILL_MAP`.

## Testing Strategy

### Unit Tests (helpers/skill_contracts.py)

- `parse_contract_from_frontmatter` correctly extracts contract block from valid YAML
- `parse_contract_from_frontmatter` returns empty dict when no contract block exists
- `parse_contract_from_frontmatter` handles malformed YAML gracefully
- `parse_contract_from_frontmatter` ignores unknown contract fields
- `parse_contract_from_frontmatter` logs warning for invalid phase values
- `parse_contract_from_frontmatter` logs warning for invalid next_skills references
- `build_skill_graph` builds graph from all installed skills with contracts
- `build_skill_graph` includes skills without contracts as empty entries
- `build_skill_graph` detects and removes cycles, logging warnings
- `build_skill_graph` caches result for subsequent calls
- `get_skill_contract` returns contract data for known skills
- `get_skill_contract` returns None for skills without contracts
- `get_next_skills` returns correct next-skill list
- `get_next_skills` returns empty list for skills without contracts
- `get_skills_for_phase` returns all contract-bearing skills for a phase
- `get_lifecycle_chain` returns the recommended chain through all phases
- `validate_graph` reports cycles, broken references, and orphans
- `validate_graph` returns empty list for a clean graph

### Unit Tests (graph queries)

- Lifecycle chain follows: spec → plan → build → verify → review → ship
- No circular dependencies in core lifecycle chain
- Conflicts are correctly reported
- Broken references (next_skills pointing to non-existent skills) are detected
- Graph rebuild works after cache invalidation

### Behavioral Tests (enforcer integration)

- Enforcer includes next-skill recommendation in correction message when contract has `next_skills`
- Enforcer does not include next-skill recommendation when skill has no contract
- Enforcer detects conflict between loaded skill and candidate skill
- Enforcer uses contract phase instead of PHASE_SKILL_MAP when they differ
- When `skill_contracts_enabled: false`, enforcer behaves exactly as Slice 3
- Telemetry `gate_decision` events include `recommended_next` field when available
- Telemetry events omit `recommended_next` when skill has no contract

### Behavioral Tests (rehydration)

- Rehydrated state includes next-skill hints when a contract-bearing skill is loaded
- Rehydrated state omits next-skill hints when no contract-bearing skill is loaded
- Rehydrated state omits next-skill hints when `skill_next_skill_hints: false`

### Regression Tests

- All existing Slice 1–3 tests pass unchanged (550+ tests green)
- Skills without contracts load and function identically to pre-Slice-4
- Existing skill search, prefilter, and classify behavior unchanged

## Boundaries

### Always

- Keep contracts optional — skills without contracts work perfectly.
- Derive the dependency graph from metadata, not hardcoded lists.
- Wrap all new logic in fail-safe try/except.
- Use existing `workflow_state` and `phase_governance` helpers for state I/O.
- Log contract parsing warnings, never raise exceptions.
- Cache the graph for the session; rebuild on demand if needed.

### Ask First

- Adding contracts to non-core skills beyond the 12 MVP skills.
- Changing the contract schema (adding required fields).
- Making the graph persistent across sessions.
- Using the graph for anything beyond enforcement and guidance (e.g., skill installation).

### Never

- Edit core framework files.
- Make contracts required for skill loading.
- Hardcode the dependency graph.
- Introduce new external dependencies.
- Break backward compatibility with Slices 1–3.

## Success Criteria (testable)

1. All 12 core lifecycle skills have valid contract blocks in their SKILL.md files (asserted).
2. The contract parser correctly extracts contract data from frontmatter and returns empty data for skills without contracts (asserted).
3. The dependency graph is built from contract metadata and contains all 12 core skills (asserted).
4. No circular dependencies exist in the core lifecycle chain (asserted by `validate_graph`).
5. The enforcer includes next-skill recommendations in correction messages when the corrected skill has `next_skills` (asserted).
6. The enforcer detects and warns about conflicts between loaded and candidate skills (asserted).
7. Contract phase takes precedence over `PHASE_SKILL_MAP` when they differ (asserted).
8. When `skill_contracts_enabled: false`, the enforcer behaves exactly as Slice 3 — zero behavioral change (asserted).
9. Rehydrated state includes next-skill hints when a contract-bearing skill is loaded and `skill_next_skill_hints: true` (asserted).
10. Telemetry events include `recommended_next` field when available (asserted).
11. All existing 550 tests remain green — no regressions.
12. Skills without contracts load, search, and function identically to pre-Slice-4 behavior (asserted).

## Open Questions

1. Should contracts be added to the remaining 11 non-core skills in a follow-up, or left as community contributions? (MVP: 12 core skills only.)
2. Should the dependency graph be persisted to `.a0proj/state/` for faster cold-start, or always rebuilt at runtime? (MVP: always rebuild — fast enough for 23 skills.)
3. Should artifact-based phase inference trigger automatic phase transitions, or only inform enforcement? (MVP: inform enforcement only — no automatic transitions.)
4. Should the `validate_graph` results be surfaced to operators, or only logged? (MVP: logged and queryable, not surfaced in UI.)
