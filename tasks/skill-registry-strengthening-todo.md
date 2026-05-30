# TODO: Skill Registry Strengthening

> Generated from:
> - `/a0/usr/projects/a0_agent_skills/docs/specs/skill-registry-strengthening-spec.md`
> - `/a0/usr/projects/a0_agent_skills/docs/plans/skill-registry-strengthening-plan.md`
>
> **Status in broader roadmap:** This file tracks **Phase 4 / Slice 4 (final)** only.
> The umbrella roadmap tracker is:
> - `/a0/usr/projects/a0_agent_skills/tasks/a0-agent-skills-workflow-governance-todo.md`

## Current decisions

- Skill registry strengthening lives entirely in **`/a0/usr/plugins/a0_agent_skills`** — no core edits
- Contracts live in **existing YAML frontmatter** of SKILL.md files under a `contract:` key — no new file format
- All contract fields are **optional** — skills without contracts load and function identically
- The dependency graph is **runtime-built** from contract metadata — never hardcoded
- The graph is a **DAG** — no circular dependencies among core lifecycle skills
- **12 core lifecycle skills** receive contracts in the MVP; 11 non-core skills remain unchanged
- Contract phase **overrides** `PHASE_SKILL_MAP` when they differ
- Next-skill guidance is **advisory** — surfaced in telemetry, rehydration, and correction messages
- New helper module: **`helpers/skill_contracts.py`** — owns parsing, graph, queries
- All extensions are fail-safe — top-level `try/except`, never break the loop
- All imports use **importlib pattern** from Slice 1
- Backward compatible: when `skill_contracts_enabled: false`, behaves exactly as Slice 3

## Phase 1: Contract parsing infrastructure

### Task 1: Create `helpers/skill_contracts.py` with contract parsing
- [x] Create new helper module `helpers/skill_contracts.py`
- [x] Define internal graph data structure: `dict[str, dict]` keyed by skill name
- [x] Implement `parse_contract_from_frontmatter(frontmatter_text)`
  - [x] Extract `contract` block from parsed YAML frontmatter
  - [x] Return empty dict when no contract block exists
  - [x] Handle malformed YAML gracefully (return empty dict)
  - [x] Ignore unknown contract fields (forward-compatible)
  - [x] Validate `phase` field: must be one of DEFINE/PLAN/BUILD/VERIFY/REVIEW/SHIP
  - [x] Log warning for invalid `phase` values, treat as None
  - [x] Validate `next_skills` entries: must reference existing skill names
  - [x] Log warning for invalid `next_skills` references, skip invalid entries
  - [x] Normalize missing fields to empty lists / None
  - [x] All functions are fail-safe — exceptions return safe defaults
- [x] Implement `read_skill_frontmatter(skill_name)`
  - [x] Locate skill directory and read SKILL.md
  - [x] Extract YAML frontmatter between `---` delimiters
  - [x] Return parsed YAML dict or empty dict on failure
- [x] Focused unit tests in `tests/test_skill_contracts.py`
  - [x] Valid full contract (all 6 fields) → parsed correctly
  - [x] Partial contract (only `phase` and `next_skills`) → missing fields normalized
  - [x] No contract block → empty dict
  - [x] Malformed YAML → empty dict
  - [x] Unknown fields → ignored, known fields extracted
  - [x] Invalid phase value → warning logged, phase treated as None
  - [x] Invalid next_skills reference → warning logged, entry skipped
  - [x] `read_skill_frontmatter` with mock skill directory → correct dict
  - [x] `read_skill_frontmatter` with missing file → empty dict

**Acceptance criteria:**
- [x] `pytest tests/test_skill_contracts.py -v` — all green
- [x] Contract parser handles all valid, partial, missing, and malformed cases
- [x] Existing 550 tests remain green

**Spec ref:** Skill Contract Format, Backward Compatibility Rules
**Plan ref:** Task 1

### Phase 1 checkpoint
- [x] `pytest tests/test_skill_contracts.py -v` — all green
- [x] Contract parser handles all edge cases
- [x] Existing 550 tests remain green

---

## Phase 2: Skill contract authoring

### Task 2: Add contract blocks to 12 core lifecycle SKILL.md files
- [x] Add `contract:` block to `skills/interview-me/SKILL.md`
  - [x] `phase: DEFINE`
  - [x] `inputs`: [User request or idea, Existing project context]
  - [x] `artifacts`: [{path: "docs/specs/*.md", description: "Clarified requirements"}]
  - [x] `verification`: [Requirements are explicit and actionable]
  - [x] `next_skills`: [spec-driven-development]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/spec-driven-development/SKILL.md`
  - [x] `phase: DEFINE`
  - [x] `inputs`: [User request or task description, Existing context about the project or feature]
  - [x] `artifacts`: [{path: "docs/specs/*.md", description: "Structured specification document"}]
  - [x] `verification`: [Spec document exists, Spec contains required sections, Spec has been reviewed]
  - [x] `next_skills`: [planning-and-task-breakdown]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/planning-and-task-breakdown/SKILL.md`
  - [x] `phase: PLAN`
  - [x] `inputs`: [Specification or requirements document, Project context]
  - [x] `artifacts`: [{path: "docs/plans/*.md", description: "Implementation plan"}, {path: "tasks/*.md", description: "Task checklist"}]
  - [x] `verification`: [Plan document exists, Tasks are broken down, Dependencies identified]
  - [x] `next_skills`: [incremental-implementation, test-driven-development]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/context-engineering/SKILL.md`
  - [x] `phase: PLAN`
  - [x] `inputs`: [Codebase structure, Task description]
  - [x] `artifacts`: [{path: ".a0proj/context/*", description: "Context index"}]
  - [x] `verification`: [Context files created, Index is queryable]
  - [x] `next_skills`: [incremental-implementation]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/incremental-implementation/SKILL.md`
  - [x] `phase: BUILD`
  - [x] `inputs`: [Implementation plan or task list, Specification or requirements]
  - [x] `artifacts`: [{path: "src/**", description: "Implemented code"}]
  - [x] `verification`: [Each slice compiles, Each slice has tests, Slices land sequentially]
  - [x] `next_skills`: [test-driven-development, debugging-and-error-recovery]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/test-driven-development/SKILL.md`
  - [x] `phase: BUILD`
  - [x] `inputs`: [Code to test or implement, Expected behavior description]
  - [x] `artifacts`: [{path: "tests/**", description: "Test files"}]
  - [x] `verification`: [Tests pass, Coverage meets threshold, Edge cases covered]
  - [x] `next_skills`: [debugging-and-error-recovery]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/source-driven-development/SKILL.md`
  - [x] `phase: BUILD`
  - [x] `inputs`: [Library or framework documentation, Task description]
  - [x] `artifacts`: [{path: "src/**", description: "Framework-aligned code"}]
  - [x] `verification`: [Code follows official patterns, API usage is correct]
  - [x] `next_skills`: [test-driven-development]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/doubt-driven-development/SKILL.md`
  - [x] `phase: BUILD`
  - [x] `inputs`: [Decision or code to review, Adversarial review context]
  - [x] `artifacts`: [{path: "**", description: "Reviewed and hardened code"}]
  - [x] `verification`: [Decision reviewed from fresh context, Risks identified]
  - [x] `next_skills`: [test-driven-development]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/debugging-and-error-recovery/SKILL.md`
  - [x] `phase: VERIFY`
  - [x] `inputs`: [Failing test or error report, Relevant code and logs]
  - [x] `artifacts`: [{path: "**", description: "Fixed code"}, {path: "tests/**", description: "Regression tests"}]
  - [x] `verification`: [Root cause identified, Fix applied, Tests pass]
  - [x] `next_skills`: [code-review-and-quality]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/browser-testing-with-devtools/SKILL.md`
  - [x] `phase: VERIFY`
  - [x] `inputs`: [Browser-based feature or UI, Expected behavior]
  - [x] `artifacts`: [{path: "tests/**", description: "Browser test files"}]
  - [x] `verification`: [Tests run in real browser, Visual and functional checks pass]
  - [x] `next_skills`: [code-review-and-quality]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/code-review-and-quality/SKILL.md`
  - [x] `phase: REVIEW`
  - [x] `inputs`: [Code changes to review, Diff or PR description]
  - [x] `artifacts`: [{path: "docs/reviews/*.md", description: "Review report"}]
  - [x] `verification`: [Five-axis review complete, Findings addressed]
  - [x] `next_skills`: [shipping-and-launch]
  - [x] `conflicts`: []
- [x] Add `contract:` block to `skills/shipping-and-launch/SKILL.md`
  - [x] `phase: SHIP`
  - [x] `inputs`: [Reviewed and approved code, Deployment target configuration]
  - [x] `artifacts`: [{path: "**", description: "Deployed artifacts"}]
  - [x] `verification`: [Pre-launch checklist complete, Deployment verified, Rollback plan exists]
  - [x] `next_skills`: []
  - [x] `conflicts`: []
- [x] Verify all 12 contracts parse without warnings using Task 1 parser
- [x] Verify `next_skills` entries reference installed skills
- [x] Verify no cycles in declared next_skills chain
- [x] Spot-check 3 SKILL.md files for well-formed YAML
- [x] Verify skills still load via `skills_tool search`

**Acceptance criteria:**
- [x] All 12 core skills have valid contract blocks
- [x] Contract parser reads all 12 without warnings
- [x] No cycles in declared next_skills chain
- [x] SKILL.md files remain valid YAML
- [x] Skills still load correctly

**Spec ref:** Skills Receiving Contracts (MVP), Skill Contract Format
**Plan ref:** Task 2

### Phase 2 checkpoint
- [x] All 12 core skills have contract blocks
- [x] Contract parser reads all 12 without warnings
- [x] No cycles in declared next_skills chain
- [x] Existing 550 tests remain green

---

## Phase 3: Graph building and queries

### Task 3: Add graph building, validation, and query functions
- [x] Extend `helpers/skill_contracts.py` with graph construction
  - [x] Implement `build_skill_graph()`
    - [x] Scan all installed skill directories for SKILL.md files
    - [x] Parse contracts from each skill
    - [x] Build graph dict: `{skill_name: {phase, next_skills, conflicts, ...}}`
    - [x] Include skills without contracts as empty entries
    - [x] Cache result in module-level variable
  - [x] Implement `invalidate_graph_cache()`
    - [x] Clear cached graph dict
    - [x] Force rebuild on next `build_skill_graph()` call
  - [x] Implement `validate_graph()`
    - [x] Check for cycles in core lifecycle chain (DFS traversal)
    - [x] Check for broken references (next_skills pointing to non-existent skills)
    - [x] Return list of finding dicts: `{"type": "cycle"|"broken_ref", "details": ...}`
    - [x] Return empty list for a clean graph
    - [x] If `skill_graph_validate_on_build: true`, run during build and remove cycle edges
  - [x] Implement query functions:
    - [x] `get_skill_contract(skill_name)` → contract dict or None
    - [x] `get_next_skills(skill_name)` → list of next skill names (empty for no contract)
    - [x] `get_skill_conflicts(skill_name)` → list of conflicting skill names
    - [x] `get_skills_for_phase(phase)` → list of contract-bearing skills with data
    - [x] `get_lifecycle_chain()` → recommended chain through all 6 phases
  - [x] All functions are fail-safe — exceptions return safe defaults
- [x] Focused unit tests in `tests/test_skill_graph.py`
  - [x] `build_skill_graph` with full installed skills → graph contains all 23 skills
  - [x] Skills without contracts appear as empty entries in graph
  - [x] Cache works: second call returns same object
  - [x] Cache invalidation: `invalidate_graph_cache()` forces rebuild
  - [x] `validate_graph` with clean graph → empty list
  - [x] `validate_graph` with injected cycle → detected and reported
  - [x] `validate_graph` with injected broken ref → detected and reported
  - [x] `get_skill_contract` for known skill → contract dict
  - [x] `get_skill_contract` for unknown skill → None
  - [x] `get_skill_contract` for skill without contract → None
  - [x] `get_next_skills` for skill with next_skills → correct list
  - [x] `get_next_skills` for skill without contract → empty list
  - [x] `get_skills_for_phase` for all 6 phases → correct skill lists
  - [x] `get_skills_for_phase("DEFINE")` → [interview-me, spec-driven-development]
  - [x] `get_skills_for_phase("BUILD")` → [incremental-impl, tdd, source-driven, doubt-driven]
  - [x] `get_lifecycle_chain` → chain through DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP
  - [x] Lifecycle chain has no cycles (explicit assertion)
  - [x] `get_skill_conflicts` for skill with conflicts → correct list
  - [x] `get_skill_conflicts` for skill without conflicts → empty list

**Acceptance criteria:**
- [x] `pytest tests/test_skill_graph.py -v` — all green
- [x] `pytest tests/test_skill_contracts.py -v` — all green
- [x] Graph builds from contract metadata
- [x] No cycles in core lifecycle chain
- [x] All query functions return correct results
- [x] Existing 550 tests remain green

**Spec ref:** Dependency Graph, Graph Queries, No Circular Dependencies
**Plan ref:** Task 3

### Phase 3 checkpoint
- [x] `pytest tests/test_skill_graph.py -v` — all green
- [x] Graph builds from contract metadata
- [x] No cycles in core lifecycle chain
- [x] All query functions return correct results
- [x] Existing 550 tests remain green

---

## Phase 4: Contract-aware enforcement

### Task 4: Extend `_10_skill_enforcer.py` with contract-aware decision flow
- [x] Add `skill_contracts` to imports in the enforcer
  - [x] Import `get_skill_contract`, `get_next_skills`, `get_skill_conflicts` from `helpers.skill_contracts`
  - [x] Use importlib pattern (load via `_load_module_by_path`)
- [x] Add contract-aware decision flow in the enforcer's `execute` method
  - [x] Read `skill_contracts_enabled` from config (default: true)
  - [x] When enabled and candidate has a contract:
    - [x] Check contract phase vs. `PHASE_SKILL_MAP`: use contract phase if different
    - [x] Look up `get_next_skills` for the candidate
    - [x] Look up `get_skill_conflicts` for the candidate
    - [x] Check loaded skills for conflicts with candidate
    - [x] If conflict detected: log warning, note in correction message
    - [x] Include next-skill recommendation in correction message when `next_skills` non-empty
  - [x] When enabled but candidate has no contract: proceed as Slice 3
  - [x] When disabled: proceed with Slice 3 logic unchanged
- [x] Enrich correction message with next-skill recommendation
  - [x] Append: "After this skill, consider loading '{next}' ({phase} phase)."
  - [x] Only when `next_skills` is non-empty
  - [x] Omit entirely when skill has no contract or `next_skills` is empty
- [x] Enrich telemetry `gate_decision` events
  - [x] Add `recommended_next` field (list of skill names) when available
  - [x] Omit `recommended_next` when skill has no contract
- [x] Enforcer remains fail-safe — contract logic inside top-level try/except
  - [x] No nudge() used
  - [x] Contract exceptions don't break the enforcement loop
- [x] Behavioral tests in `tests/test_skill_enforcer.py` (extend existing)
  - [x] Correction message includes next-skill when contract has `next_skills`
  - [x] Correction message omits next-skill when skill has no contract
  - [x] Contract phase overrides `PHASE_SKILL_MAP` when they differ
  - [x] Conflict between loaded skill and candidate is detected and logged
  - [x] `skill_contracts_enabled: false` → Slice 3 behavior preserved
  - [x] Telemetry includes `recommended_next` field when available
  - [x] Telemetry omits `recommended_next` when no contract
  - [x] Source-level test: enforcer body still has top-level try/except

**Acceptance criteria:**
- [x] `pytest tests/test_skill_enforcer.py -v` — all green (including new contract-aware tests)
- [x] Correction messages include next-skill recommendations
- [x] Conflicts are detected and logged
- [x] Telemetry includes `recommended_next` when available
- [x] Existing tests remain green

**Spec ref:** Contract-Aware Enforcement, Next-Skill Guidance, Enhanced Correction Message
**Plan ref:** Task 4

### Phase 4 checkpoint
- [x] `pytest tests/test_skill_enforcer.py -v` — all green
- [x] Correction messages include next-skill recommendations
- [x] Conflicts are detected and logged
- [x] Existing tests remain green

---

## Phase 5: Next-skill hints in rehydration

### Task 5: Extend `_67_reattach_workflow_state.py` with next-skill hints
- [x] Add `skill_contracts` to imports in the rehydration extension
  - [x] Import `get_next_skills`, `get_skill_contract`, `build_skill_graph` from `helpers.skill_contracts`
  - [x] Use importlib pattern
- [x] Add next-skill hints section to rehydrated state block
  - [x] Read `skill_next_skill_hints` from config (default: true)
  - [x] When enabled and loaded skills include contract-bearing skills:
    - [x] For each loaded skill with a contract, look up `get_next_skills`
    - [x] Build hints: "After {skill}: consider loading {next_skill} ({phase} phase)"
    - [x] Append "Next skill hints:" section to rehydrated state block
  - [x] When no loaded skills have contracts: omit section entirely
  - [x] When `skill_next_skill_hints: false`: omit section entirely
  - [x] When graph not built yet: call `build_skill_graph()` on demand
  - [x] Extension remains fail-safe — graph lookup exceptions don't break rehydration
- [x] Behavioral tests in `tests/test_workflow_state.py` (extend existing)
  - [x] Rehydrated state includes hints when contract-bearing skill is loaded
  - [x] Rehydrated state omits hints when no contract-bearing skill is loaded
  - [x] Rehydrated state omits hints when `skill_next_skill_hints: false`
  - [x] Hints section format matches spec: "- After {skill}: consider loading {next} ({phase} phase)"
  - [x] Graph build on demand works when graph is not yet built
  - [x] Fail-safe: graph exception does not break rehydration

**Acceptance criteria:**
- [x] Rehydrated state includes next-skill hints when appropriate
- [x] Existing rehydration behavior preserved
- [x] `pytest tests/test_workflow_state.py -v` — all green
- [x] Existing tests remain green

**Spec ref:** Next-Skill Guidance, Rehydration State Extension
**Plan ref:** Task 5

### Phase 5 checkpoint
- [x] Rehydrated state includes next-skill hints when appropriate
- [x] Existing rehydration behavior preserved
- [x] Existing tests remain green

---

## Phase 6: Config and telemetry

### Task 6: Add config keys and enrich telemetry
- [x] Add config keys to `default_config.yaml`
  - [x] `skill_contracts_enabled: true` with comment: "# Set to false to disable contract parsing and graph building"
  - [x] `skill_graph_validate_on_build: true` with comment: "# Validate graph for cycles on construction"
  - [x] `skill_next_skill_hints: true` with comment: "# Include next-skill hints in rehydration and telemetry"
- [x] Config-disabled behavioral tests
  - [x] `skill_contracts_enabled: false` → enforcer behaves as Slice 3 (no contract lookups)
  - [x] `skill_next_skill_hints: false` → rehydration omits hints section
  - [x] `skill_graph_validate_on_build: false` → graph builds without running validation
- [x] Verify telemetry `gate_decision` events include `recommended_next` when available
- [x] Verify telemetry events omit `recommended_next` when skill has no contract

**Acceptance criteria:**
- [x] Config file has new keys with sensible defaults and comments
- [x] Config-disabled behavioral tests pass
- [x] Telemetry enrichment verified
- [x] Existing tests remain green

**Spec ref:** Config Surface, Telemetry Event Extension
**Plan ref:** Task 6

### Phase 6 checkpoint
- [x] Config file updated with new keys
- [x] Config-disabled behavior verified
- [x] Telemetry enrichment verified
- [x] Existing tests remain green

---

## Phase 7: Integration verification

### Task 7: Integration verification and regression testing
- [x] Run full plugin suite: `python -m pytest tests/ --tb=short`
  - [x] All tests pass (550+ baseline + new Slice 4 tests)
  - [x] No failures, no unexpected skips
- [x] Verify all 12 core skills load correctly with contract blocks
  - [x] Parse each with contract parser → no warnings
- [x] Verify all 11 non-core skills load correctly without contract blocks
  - [x] Parse each → empty contract dict, no warnings
- [x] Verify dependency graph builds without errors
  - [x] `build_skill_graph()` returns complete graph
  - [x] `validate_graph()` returns empty list (clean)
- [x] Verify lifecycle chain is correct
  - [x] DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP
  - [x] No cycles (explicit assertion)
- [x] Verify no behavioral regressions
  - [x] Enforcement gate works as expected (observe + enforce modes)
  - [x] Workflow state persists and rehydrates correctly
  - [x] Phase-aware governance works as expected
- [x] Manual spot-checks
  - [x] Read 2 SKILL.md files, confirm contract blocks present and well-formed
  - [x] Trigger enforcer in observe mode, confirm `recommended_next` appears in telemetry

**Acceptance criteria:**
- [x] Full test suite green (550+ baseline + new tests)
- [x] All 12 core skills have contracts
- [x] Dependency graph is acyclic and complete
- [x] Next-skill guidance appears in corrections, telemetry, and rehydration
- [x] Skills without contracts work identically to pre-Slice-4
- [x] Ready for umbrella roadmap closure

**Spec ref:** Success Criteria, Testing Strategy
**Plan ref:** Task 7

### Final checkpoint
- [x] Full test suite green
- [x] All 12 core skills have contracts
- [x] Dependency graph is acyclic and complete
- [x] Next-skill guidance appears in corrections, telemetry, and rehydration
- [x] Skills without contracts work identically to pre-Slice-4
- [x] Ready for umbrella roadmap closure

---

## Notes

- Planning/spec/docs live in **`/a0/usr/projects/a0_agent_skills`**
- Implementation lives in **`/a0/usr/plugins/a0_agent_skills`**
- Do not confuse the umbrella roadmap with the current slice
- Do not broaden scope into `_permissions` or `_tracing`
- Contracts are optional — never make them required for skill loading
- Graph is derived from metadata — never hardcode the dependency graph
