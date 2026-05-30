# Implementation Plan: Skill Registry Strengthening

> Generated from spec `docs/specs/skill-registry-strengthening-spec.md`.
>
> **Status in broader roadmap:** This is the **Phase 4 / Slice 4 (final)** implementation plan under the umbrella workflow-governance roadmap.
> For the broader roadmap, see:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

## Overview

This plan implements **skill registry strengthening** for `a0_agent_skills`, adding rich contract metadata to core engineering skills and building a runtime dependency graph for next-skill guidance.

The feature has two main components:

1. **Skill contract support** — a contract parsing helper and contract blocks added to 12 core lifecycle SKILL.md files, enabling machine-readable declarations of phase, inputs, artifacts, verification steps, next skills, and conflicts.
2. **Dependency graph and next-skill guidance** — a runtime DAG built from contract metadata, queried by the enforcer and rehydration extension to provide next-skill recommendations.

The implementation follows the same principles as Slices 1–3:

1. **User-space only** — all implementation lives in `/a0/usr/plugins/a0_agent_skills`; no core framework edits.
2. **Fail-safe extensions** — all extension bodies wrapped in try/except; contract parsing failures never break the agent loop.
3. **Additive, not replacing** — contract-awareness extends the existing enforcer; it does not replace the prefilter/classify/phase-aware flow.
4. **Backward compatible** — skills without contracts load and function identically to pre-Slice-4 behavior.
5. **Measure everything** — focused tests for every new behavior before broad rollout.

## Architecture Decisions

- **Contracts in YAML frontmatter:** Contract metadata lives inside the existing `---` frontmatter block of each `SKILL.md` file under a `contract:` key. No new file format. Backward compatible — skills without `contract:` load normally.
- **New helper module:** `helpers/skill_contracts.py` owns contract parsing, graph building, graph queries, and graph validation. It does NOT own state I/O — that remains in `helpers/workflow_state.py`.
- **Graph is runtime-built, not hardcoded:** The dependency graph is constructed from contract metadata every time it is first needed, then cached for the session. This means it is always consistent with installed skills.
- **Contract phase overrides map phase:** If a skill declares a `contract.phase` that differs from its assignment in `PHASE_SKILL_MAP`, the contract wins. This allows skills to self-declare without modifying the hardcoded map.
- **Next-skill guidance is advisory:** Recommendations appear in correction messages, telemetry, and rehydrated state. They never block or force skill loading.
- **12 core skills receive contracts in MVP:** The remaining 11 skills continue to function via `PHASE_SKILL_MAP` only.
- **No circular dependencies:** The graph validator checks for cycles in the core lifecycle chain and removes them with a warning.

## Dependency Graph

```text
Slice 3 complete (550 tests passing)
   │
   ├── Task 1: Contract parsing helper + graph data structure
   │       │
   │       ├── Task 2: Add contract blocks to 12 core lifecycle skills
   │       │       │
   │       │       └── Task 3: Graph building + validation + queries
   │       │               │
   │       │               └── Task 4: Contract-aware enforcer integration
   │       │                       │
   │       │                       └── Task 5: Next-skill hints in rehydration
   │       │
   │       └── Task 6: Config surface + telemetry enrichment
   │               │
   │               └── Task 7: Integration verification + regression
   │
   └── Full regression verification
```

## Task List

### Phase 1: Contract Parsing Infrastructure

## Task 1: Create `helpers/skill_contracts.py` with contract parsing

**Description:**
Build the contract parsing helper module. This module provides functions to parse YAML frontmatter from SKILL.md files, extract contract blocks, validate contract fields, and serve as the foundation for graph building.

**Acceptance criteria:**
- [ ] `parse_contract_from_frontmatter(frontmatter_text)` extracts contract block from valid YAML
- [ ] `parse_contract_from_frontmatter` returns empty dict when no contract block exists
- [ ] `parse_contract_from_frontmatter` handles malformed YAML gracefully (returns empty dict)
- [ ] `parse_contract_from_frontmatter` ignores unknown contract fields (forward-compatible)
- [ ] `parse_contract_from_frontmatter` logs warning for invalid `phase` values
- [ ] `parse_contract_from_frontmatter` logs warning for invalid `next_skills` references (non-existent skills)
- [ ] `parse_contract_from_frontmatter` normalizes missing fields to empty lists/None
- [ ] `read_skill_frontmatter(skill_name)` reads frontmatter from a skill's SKILL.md
- [ ] All functions are fail-safe — exceptions return safe defaults, never raise
- [ ] Internal graph data structure defined: `dict[str, dict]` keyed by skill name

**Verification:**
- [ ] Focused unit tests in `tests/test_skill_contracts.py`
- [ ] `parse_contract_from_frontmatter` tested with:
  - [ ] Valid full contract (all 6 fields)
  - [ ] Partial contract (only `phase` and `next_skills`)
  - [ ] No contract block → empty dict
  - [ ] Malformed YAML → empty dict
  - [ ] Unknown fields → ignored, known fields extracted
  - [ ] Invalid phase value → warning logged, phase treated as None
  - [ ] Invalid next_skills reference → warning logged, entry skipped
- [ ] `read_skill_frontmatter` tested with mock skill directory
- [ ] All tests use `importlib` import pattern

**Dependencies:** Slice 3 complete

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/skill_contracts.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_contracts.py` (new)

**Estimated scope:** Medium (foundational — Tasks 3–6 depend on this)

### Checkpoint: After Task 1

- [ ] `pytest tests/test_skill_contracts.py -v` — all green
- [ ] Contract parser handles all valid, partial, missing, and malformed cases
- [ ] Existing 550 tests remain green

---

### Phase 2: Skill Contract Authoring

## Task 2: Add contract blocks to 12 core lifecycle SKILL.md files

**Description:**
Add `contract:` blocks to the YAML frontmatter of 12 core lifecycle skills. Each contract declares phase, inputs, artifacts, verification steps, next_skills, and conflicts.

**Skills to update (with contracts):**

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

**Acceptance criteria:**
- [ ] All 12 skills have valid YAML frontmatter with `contract:` block
- [ ] Each contract has: `phase`, `inputs`, `artifacts`, `verification`, `next_skills`, `conflicts`
- [ ] Contract phase matches `PHASE_SKILL_MAP` assignment for each skill
- [ ] `next_skills` entries reference existing skill names
- [ ] SKILL.md files remain valid YAML frontmatter (no syntax errors)
- [ ] Skills still load correctly via `skills_tool`

**Verification:**
- [ ] Parse each updated SKILL.md with the contract parser from Task 1
- [ ] Verify all 12 contracts parse without warnings
- [ ] Verify `next_skills` entries reference installed skills
- [ ] Verify no cycles in the declared next_skills chain
- [ ] Spot-check: read 3 updated SKILL.md files and confirm contract block is well-formed
- [ ] Run `skills_tool search` for each skill and confirm it still loads

**Dependencies:** Task 1 (parser must exist to verify contracts)

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/skills/interview-me/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/spec-driven-development/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/planning-and-task-breakdown/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/context-engineering/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/incremental-implementation/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/test-driven-development/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/source-driven-development/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/doubt-driven-development/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/debugging-and-error-recovery/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/browser-testing-with-devtools/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/code-review-and-quality/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/shipping-and-launch/SKILL.md`

**Estimated scope:** Medium (12 files, but each change is small and templated)

### Checkpoint: After Task 2

- [ ] All 12 core skills have contract blocks
- [ ] Contract parser reads all 12 without warnings
- [ ] No cycles in declared next_skills chain
- [ ] Existing 550 tests remain green

---

### Phase 3: Graph Building and Queries

## Task 3: Add graph building, validation, and query functions

**Description:**
Extend `helpers/skill_contracts.py` with graph construction, cycle detection, and query functions. The graph is a DAG built from the `next_skills` fields of all installed skill contracts.

**Acceptance criteria:**
- [ ] `build_skill_graph()` scans all installed skills, parses contracts, builds graph dict
- [ ] Graph includes skills without contracts as empty entries
- [ ] `build_skill_graph()` caches result; subsequent calls return cached graph
- [ ] `invalidate_graph_cache()` clears the cache for forced rebuild
- [ ] `validate_graph()` checks for:
  - [ ] Cycles in the core lifecycle chain
  - [ ] Broken references (`next_skills` pointing to non-existent skills)
  - [ ] Returns list of finding dicts: `{"type": "cycle"|"broken_ref", "details": ...}`
  - [ ] Returns empty list for a clean graph
- [ ] If `skill_graph_validate_on_build: true`, validation runs during build and cycle edges are removed
- [ ] `get_skill_contract(skill_name)` returns contract dict or None
- [ ] `get_next_skills(skill_name)` returns list of next skill names
- [ ] `get_next_skills` returns empty list for skills without contracts
- [ ] `get_skill_conflicts(skill_name)` returns list of conflicting skill names
- [ ] `get_skills_for_phase(phase)` returns list of contract-bearing skills for a phase
- [ ] `get_lifecycle_chain()` returns the recommended chain through all 6 phases
- [ ] All functions are fail-safe

**Verification:**
- [ ] Focused unit tests in `tests/test_skill_graph.py`
- [ ] `build_skill_graph` tested with:
  - [ ] Full set of installed skills (12 with contracts, 11 without)
  - [ ] Skills without contracts appear as empty entries
  - [ ] Cache works (second call returns same object)
  - [ ] Cache invalidation forces rebuild
- [ ] `validate_graph` tested with:
  - [ ] Clean graph → empty list
  - [ ] Injected cycle → detected and reported
  - [ ] Injected broken ref → detected and reported
- [ ] `get_skill_contract` tested for known and unknown skills
- [ ] `get_next_skills` tested for skills with and without contracts
- [ ] `get_skills_for_phase` tested for all 6 phases
- [ ] `get_lifecycle_chain` returns expected chain
- [ ] Lifecycle chain has no cycles (explicit assertion)

**Dependencies:** Tasks 1, 2

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/skill_contracts.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_graph.py` (new)

**Estimated scope:** Medium-large (core infrastructure — many query paths to test)

### Checkpoint: After Task 3

- [ ] `pytest tests/test_skill_graph.py -v` — all green
- [ ] `pytest tests/test_skill_contracts.py -v` — all green
- [ ] Graph builds from contract metadata
- [ ] No cycles in core lifecycle chain
- [ ] Existing 550 tests remain green

---

### Phase 4: Contract-Aware Enforcement

## Task 4: Extend `_10_skill_enforcer.py` with contract-aware decision flow

**Description:**
Broaden the existing enforcement gate to read contract data, include next-skill recommendations in corrections, detect conflicts, and use contract phase instead of map phase when they differ.

**Acceptance criteria:**
- [ ] Enforcer reads `skill_contracts_enabled` from config
- [ ] When `skill_contracts_enabled: true` and candidate has a contract:
  - [ ] If candidate's contract phase differs from `PHASE_SKILL_MAP`, use contract phase
  - [ ] Include next-skill recommendation in correction message (when `next_skills` is non-empty)
  - [ ] Check for conflicts between loaded skills and candidate
  - [ ] If conflict detected: log warning, still proceed with correction but note the conflict
- [ ] When `skill_contracts_enabled: true` but candidate has no contract: proceed as Slice 3
- [ ] When `skill_contracts_enabled: false`: behave exactly as Slice 3
- [ ] Correction message includes next-skill recommendation when available:
  ```
  After this skill, consider loading 'debugging-and-error-recovery' (VERIFY phase).
  ```
- [ ] Telemetry `gate_decision` events include `recommended_next` field when available
- [ ] Telemetry events omit `recommended_next` when skill has no contract
- [ ] Enforcer remains fail-safe — contract logic exceptions don't break the loop

**Verification:**
- [ ] Behavioral tests in `tests/test_skill_enforcer.py` (extend existing):
  - [ ] Correction message includes next-skill when contract has `next_skills`
  - [ ] Correction message omits next-skill when skill has no contract
  - [ ] Contract phase overrides `PHASE_SKILL_MAP` when they differ
  - [ ] Conflict between loaded skill and candidate is detected and logged
  - [ ] `skill_contracts_enabled: false` → Slice 3 behavior preserved
  - [ ] Telemetry includes `recommended_next` field when available
  - [ ] Telemetry omits `recommended_next` when no contract
- [ ] Source-level test: enforcer body still has top-level try/except
- [ ] No nudge() used

**Dependencies:** Tasks 1, 3

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_before/_10_skill_enforcer.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py` (extend)

**Estimated scope:** Large (core behavioral change — needs thorough testing)

### Checkpoint: After Task 4

- [ ] `pytest tests/test_skill_enforcer.py -v` — all green (including new contract-aware tests)
- [ ] Correction messages include next-skill recommendations
- [ ] Conflicts are detected and logged
- [ ] Existing tests remain green

---

### Phase 5: Next-Skill Hints in Rehydration

## Task 5: Extend `_67_reattach_workflow_state.py` with next-skill hints

**Description:**
Extend the rehydration extension to include next-skill recommendations in the rehydrated state block when a contract-bearing skill is loaded and `skill_next_skill_hints: true`.

**Acceptance criteria:**
- [ ] Rehydration extension reads `skill_next_skill_hints` from config
- [ ] When enabled and a contract-bearing skill is loaded:
  - [ ] Look up `get_next_skills` for each loaded skill
  - [ ] Include "Next skill hints" section in rehydrated state block
  - [ ] Format: `- After {skill}: consider loading {next_skill} ({phase} phase)`
- [ ] When no loaded skills have contracts: omit "Next skill hints" section
- [ ] When `skill_next_skill_hints: false`: omit section entirely
- [ ] When graph is not built yet: build on demand (first rehydration triggers build)
- [ ] Extension remains fail-safe — graph lookup exceptions don't break rehydration

**Verification:**
- [ ] Behavioral tests in `tests/test_workflow_state.py` (extend existing):
  - [ ] Rehydrated state includes hints when contract-bearing skill loaded
  - [ ] Rehydrated state omits hints when no contract-bearing skill loaded
  - [ ] Rehydrated state omits hints when `skill_next_skill_hints: false`
  - [ ] Hints section format is correct
- [ ] Manual read of rehydrated state block confirms expected format

**Dependencies:** Tasks 3, 4

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py` (extend)

**Estimated scope:** Small-medium (additive extension to existing rehydration)

### Checkpoint: After Task 5

- [ ] Rehydrated state includes next-skill hints when appropriate
- [ ] Existing rehydration behavior preserved
- [ ] Existing tests remain green

---

### Phase 6: Config and Telemetry

## Task 6: Add config keys and enrich telemetry

**Description:**
Add config surface for skill contracts and verify that telemetry events are enriched with next-skill recommendations.

**Acceptance criteria:**
- [ ] `default_config.yaml` has new keys with sensible defaults:
  - [ ] `skill_contracts_enabled: true`
  - [ ] `skill_graph_validate_on_build: true`
  - [ ] `skill_next_skill_hints: true`
- [ ] Each key has a descriptive comment
- [ ] Config-disabled tests pass:
  - [ ] `skill_contracts_enabled: false` → enforcer behaves as Slice 3
  - [ ] `skill_next_skill_hints: false` → rehydration omits hints
  - [ ] `skill_graph_validate_on_build: false` → graph builds without validation
- [ ] Telemetry `gate_decision` events include `recommended_next` when available

**Verification:**
- [ ] Config file has new keys with comments
- [ ] Config-disabled behavioral tests pass
- [ ] Telemetry output spot-checked for `recommended_next` field

**Dependencies:** Tasks 4, 5

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/default_config.yaml` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py` (extend)

**Estimated scope:** Small

### Checkpoint: After Task 6

- [ ] Config file updated with new keys
- [ ] Config-disabled behavior verified
- [ ] Telemetry enrichment verified
- [ ] Existing tests remain green

---

### Phase 7: Integration Verification

## Task 7: Integration verification and regression testing

**Description:**
Run comprehensive regression testing to ensure Slice 4 integrates cleanly with Slices 1–3 and all 550+ existing tests remain green.

**Acceptance criteria:**
- [ ] Full plugin suite passes: `python -m pytest tests/ --tb=short`
- [ ] All 12 core skills load correctly with contract blocks
- [ ] All 11 non-core skills load correctly without contract blocks
- [ ] Dependency graph builds without errors or warnings
- [ ] `validate_graph()` returns clean (no cycles, no broken refs)
- [ ] Lifecycle chain is correct: DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP
- [ ] No behavioral regressions in enforcement, state, or phase governance

**Verification:**
- [ ] `python -m pytest tests/ --tb=short` — all green
- [ ] Test count increased from 550 baseline
- [ ] Parity report runs cleanly
- [ ] Manual spot-check: read 2 SKILL.md files, confirm contract blocks present and well-formed
- [ ] Manual spot-check: trigger enforcer in observe mode, confirm `recommended_next` appears in telemetry

**Dependencies:** Tasks 1–6

**Files likely touched:**
- None (verification only)

**Estimated scope:** Small

### Final Checkpoint

- [ ] Full test suite green (550+ baseline + new tests)
- [ ] All 12 core skills have contracts
- [ ] Dependency graph is acyclic and complete
- [ ] Next-skill guidance appears in corrections, telemetry, and rehydration
- [ ] Skills without contracts work identically to pre-Slice-4
- [ ] Ready for umbrella roadmap closure

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Contract YAML parsing breaks existing SKILL.md loading | High | Contract fields are optional; malformed YAML returns empty dict; all parsing is fail-safe |
| Dependency graph has unexpected cycles | Medium | Cycle detection runs on build; cycle edges removed with warning; `validate_graph()` is queryable |
| 12 SKILL.md edits introduce syntax errors | Medium | Each edit is small and templated; parser validates every file; spot-check 3+ files manually |
| Contract phase conflicts with `PHASE_SKILL_MAP` | Low | Contract phase takes precedence by design; mismatches are logged |
| Graph building is slow for 23 skills | Low | Timing is negligible (< 100ms for 23 skills); cache avoids repeat builds |
| Next-skill hints clutter rehydrated state | Low | Hints are conditional on config and contract presence; can be disabled |

## Open Questions

- Should contracts for the remaining 11 non-core skills be added in a follow-up slice or left as community contributions?
- Should the dependency graph be persisted to `.a0proj/state/` for faster cold-start?
- Should artifact-based phase inference trigger automatic phase transitions?
- Should `validate_graph` results be surfaced in a dedicated operator command?
