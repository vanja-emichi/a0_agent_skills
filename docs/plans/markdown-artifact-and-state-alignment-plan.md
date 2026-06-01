# Implementation Plan: Markdown Artifact and Workflow State Alignment

> Generated from spec `docs/specs/markdown-artifact-and-state-alignment-spec.md`.
>
> **Status in broader roadmap:** This plan implements artifact path alignment, state tracking,
> command modernization, and no-project support for `a0_agent_skills`.

## Overview

This plan aligns `a0_agent_skills` artifact generation, storage, and tracking with Agent Zero workspace conventions. It extends `helpers/workflow_state.py` with artifact path resolution functions (no new helper file — artifact paths are state, and `workflow_state.py` already owns all state I/O) that detect project vs. no-project mode, return canonical artifact paths for a feature slug, and persist the active artifact set in `workflow_artifacts.json`. Slash commands are updated to use the resolver instead of hardcoded legacy paths. Typed events, approval markers, artifact lifecycle states, and handoff/rehydration improvements round out the feature. The work is phased so each stage leaves the system in a working, testable state.

## Architecture Decisions

1. **Extend `helpers/workflow_state.py`** — Artifact path resolution functions added to the existing state module (no new helper file). Artifact paths are state, and `workflow_state.py` already owns all state I/O. Commands call these functions; they never join paths themselves.

2. **Standalone state file: `workflow_artifacts.json`** — Supplements (does not replace) `active_plan.json`, `active_goal.json`, and `loaded_skills.json`. Tracks feature slug, all artifact paths, approval state, and lifecycle status.

3. **No-project fallback: `/a0/usr/workdir/.a0_agent_skills/state/`** — Plugin-local state directory for when no project is active. Never creates a fake `.a0proj`.

4. **Feature slug from first artifact** — Derived from the filename of the first artifact created (e.g., `my-feature-spec.md` → slug `my-feature`). Stored in `workflow_artifacts.json`. Overridable via `--slug`.

5. **Typed events in `progress_log.jsonl`** — Events use structured schemas (`artifact_created`, `artifact_updated`, `phase_change`, `approval`, `artifact_lifecycle`). Enables replay, audit, and debugging.

6. **`markdown-documents` as companion skill** — Loaded by document-producing commands, not globally enforced. Documented in command templates and `using-agent-skills`.

7. **Legacy compatibility** — Legacy singleton paths (`SPEC.md`, `tasks/plan.md`, `tasks/todo.md`) are checked as fallbacks when no feature-scoped artifact is found.

8. **No `helpers/spec_reader.py` extraction** — Per spec decision RF2, spec-reading logic stays in `ship.py` until duplication cost clearly warrants extraction.

## Dependency Graph

```
Phase 1: Foundation (path resolver + state model)
    │
    ├── Phase 2: Event Model (typed events)
    │
    ├── Phase 3: Command Alignment (use resolver)
    │
    ├── Phase 4: Approval + Lifecycle
    │
    └── Phase 5: Rehydration + Handoff
         │
         └── Phase 6: Testing
```

Phases 2–5 all depend on Phase 1. Phase 6 depends on all previous phases.

---

## Phase 1: Foundation — Path Resolver + State Model

### Task 1.1: Extend `helpers/workflow_state.py` — Add Artifact Path Resolution

**Description:** Add artifact path resolution functions to the existing `helpers/workflow_state.py` module (no new file). These functions detect project vs. no-project mode, return canonical artifact paths for a given feature slug, and return the correct state root. They reuse existing utilities (`resolve_state_dir`, `_ensure_dir`, `_safe_read_json`, `_safe_write_json`, `_state_path`).

**Acceptance criteria:**
- [ ] `resolve_paths(context, feature_slug=None)` returns a dataclass/named tuple with `visible_root`, `state_root`, `spec_path`, `plan_path`, `todo_path`, `idea_path`, `intent_path`, `review_path`, `report_path`, `adr_dir`
- [ ] In project mode, `visible_root` is the project folder and `state_root` is `.a0proj/state/`
- [ ] In no-project mode, `visible_root` is `/a0/usr/workdir` and `state_root` is `/a0/usr/workdir/.a0_agent_skills/state/`
- [ ] `state_root` reads `default_config.yaml.workflow_state_path` when present
- [ ] All artifact paths follow the canonical naming convention (`docs/specs/<slug>-spec.md`, etc.)
- [ ] Target directories are auto-created with `mkdir -p` on path generation (not on resolution)
- [ ] Corrupted or empty state files produce a warning and return safe defaults, no crash

**Verification:**
- [ ] Unit tests pass: `pytest tests/test_workflow_state.py -v`
- [ ] Manual check: import the module in a Python REPL and call `resolve_paths` with mock context

**Dependencies:** None

**Files likely touched:**
- `helpers/workflow_state.py` (existing, extended)

**Estimated scope:** M (3–4 logical sections in one file)

---

### Task 1.2: Add `workflow_artifacts.json` State File Support

**Description:** Add read/write functions for `workflow_artifacts.json` in the existing helper. This file tracks feature slug, all artifact paths, approval state, lifecycle status, and timestamps.

**Acceptance criteria:**
- [ ] `save_workflow_artifacts(agent, data)` writes `workflow_artifacts.json` to the resolved `state_root`
- [ ] `read_workflow_artifacts(agent)` reads and returns the parsed JSON, or `None` if missing/corrupt
- [ ] The JSON schema includes: `feature_slug`, `idea_path`, `intent_path`, `spec_path`, `plan_path`, `todo_path`, `review_report_path`, `ship_report_path`, `adr_paths` (list), `phase`, `approved` (dict with `spec`, `plan` booleans), `lifecycle` (dict mapping artifact type to status), `updated_at`
- [ ] State is fully independent of `active_plan.json`, `active_goal.json`, `loaded_skills.json`
- [ ] Writing is atomic (write to temp, rename)

**Verification:**
- [ ] Unit tests: roundtrip save/read, corrupt file handling, missing state dir
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 1.1

**Files likely touched:**
- `helpers/workflow_state.py`

**Estimated scope:** S (1–2 files)

---

### Task 1.3: Add Feature Slug Discovery

**Description:** Implement slug discovery logic that derives the feature slug from the first artifact filename or from scanning existing spec files.

**Acceptance criteria:**
- [ ] `discover_slug(agent)` checks `workflow_artifacts.json` for stored slug first
- [ ] If no stored slug, scans `docs/specs/` for `*-spec.md` files
- [ ] If exactly one spec found, extracts slug from filename
- [ ] If multiple specs found, returns list for disambiguation
- [ ] If no specs found, returns `None` (command should prompt user)
- [ ] Slug extraction handles `<slug>-spec.md` pattern correctly

**Verification:**
- [ ] Unit tests: single spec → auto-discover, multiple specs → return list, no specs → None
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 1.2

**Files likely touched:**
- `helpers/workflow_state.py`

**Estimated scope:** S (1 file)

---

### Task 1.4: Update `resolve_state_dir` to Respect Config and Add No-Project Fallback

**Description:** Extend `workflow_state.resolve_state_dir()` to fall back to the no-project state directory when no project is active, and read `workflow_state_path` from config.

**Acceptance criteria:**
- [ ] When a project is active, behavior is unchanged (returns `.a0proj/state/`)
- [ ] When no project is active, returns `/a0/usr/workdir/.a0_agent_skills/state/`
- [ ] The no-project fallback directory is created lazily on first write
- [ ] `resolve_state_dir` reads `default_config.yaml.workflow_state_path` and uses it when set
- [ ] Existing tests continue to pass (no regressions)

**Verification:**
- [ ] `pytest tests/test_workflow_state.py -v` — all existing tests pass
- [ ] New test: no-project agent returns workdir fallback path
- [ ] New test: config override is respected

**Dependencies:** None (independent of Tasks 1.1–1.3)

**Files likely touched:**
- `helpers/workflow_state.py` (modify `resolve_state_dir`)
- `tests/test_workflow_state.py` (extend)

**Estimated scope:** S (2 files)

---

### Checkpoint: Phase 1

- [ ] All Phase 1 tests pass: `pytest tests/test_workflow_state.py tests/test_workflow_state.py -v`
- [ ] `resolve_paths` works for both project and no-project modes
- [ ] `workflow_artifacts.json` can be saved, read, and round-tripped
- [ ] Slug discovery works for single-spec, multi-spec, and no-spec cases
- [ ] `resolve_state_dir` falls back to no-project path
- [ ] No existing tests broken
- [ ] Review with human before proceeding

---

## Phase 2: Event Model — Typed Events

### Task 2.1: Define Typed Event Schemas

**Description:** Add event schema constants and a helper to emit typed events to `progress_log.jsonl`.

**Acceptance criteria:**
- [ ] Event types defined: `artifact_created`, `artifact_updated`, `phase_change`, `approval`, `artifact_lifecycle`
- [ ] Each event has required fields: `event`, `timestamp`, plus type-specific fields (`artifact_type`, `path`, `slug`, `from`, `to`, `decision`, `status`)
- [ ] `emit_artifact_event(agent, event_type, **kwargs)` appends a structured event to `progress_log.jsonl`
- [ ] Events use ISO 8601 timestamps
- [ ] Existing untyped progress events continue to work (no breaking change)

**Verification:**
- [ ] Unit tests: each event type produces valid JSON
- [ ] Unit test: events appended to log without corrupting existing entries
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 1.1 (uses `resolve_state_dir`)

**Files likely touched:**
- `helpers/workflow_state.py` (add event helpers)

**Estimated scope:** S (1 file)

---

### Task 2.2: Emit Events on Artifact State Changes

**Description:** Integrate event emission into the artifact save functions so that creating, updating, approving, and lifecycle-transitioning artifacts all emit typed events.

**Acceptance criteria:**
- [ ] `save_workflow_artifacts` emits `artifact_created` on new artifact or `artifact_updated` on existing
- [ ] Approval changes emit `approval` events
- [ ] Lifecycle transitions emit `artifact_lifecycle` events
- [ ] Phase changes emit `phase_change` events
- [ ] All events include the feature slug and artifact path

**Verification:**
- [ ] Unit test: creating an artifact emits `artifact_created` event
- [ ] Unit test: approving an artifact emits `approval` event
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 2.1

**Files likely touched:**
- `helpers/workflow_state.py`

**Estimated scope:** S (1 file)

---

### Checkpoint: Phase 2

- [ ] All typed events emit correctly
- [ ] Existing progress log entries are not corrupted
- [ ] Event format matches spec schema
- [ ] `pytest tests/test_workflow_state.py -v` passes

---

## Phase 3: Command Alignment — Fix Hardcoded Paths

### Task 3.1: Update `/spec` Command

**Description:** Update `commands/spec.txt` to use the artifact path resolver instead of hardcoding `SPEC.md`.

**Acceptance criteria:**
- [ ] Command template instructs agent to call `workflow_artifacts.resolve_paths()` to determine spec output path
- [ ] Default spec path is `docs/specs/<slug>-spec.md` (feature-scoped)
- [ ] Legacy `SPEC.md` is checked as a fallback if no feature slug exists
- [ ] After spec creation, `workflow_artifacts.json` is updated with spec path and slug
- [ ] `markdown-documents` skill is loaded as companion for the write
- [ ] An `artifact_created` event is emitted

**Verification:**
- [ ] Read the updated command file and verify resolver instructions present
- [ ] Manual check: run `/spec` in a test project and verify output path

**Dependencies:** Task 1.1, Task 1.2

**Files likely touched:**
- `commands/spec.txt`

**Estimated scope:** S (1 file)

---

### Task 3.2: Update `/plan` Command

**Description:** Update `commands/plan.txt` to use the artifact path resolver instead of hardcoding `tasks/plan.md` and `tasks/todo.md`.

**Acceptance criteria:**
- [ ] Command template instructs agent to call `workflow_artifacts.resolve_paths()` for plan and todo paths
- [ ] Default plan path is `docs/plans/<slug>-plan.md`
- [ ] Default todo path is `tasks/<slug>-todo.md`
- [ ] Legacy `tasks/plan.md` and `tasks/todo.md` are fallbacks
- [ ] After plan creation, `workflow_artifacts.json` is updated with plan_path and todo_path
- [ ] `markdown-documents` skill loaded as companion
- [ ] Emits `artifact_created` event

**Verification:**
- [ ] Read updated command file
- [ ] Manual check: run `/plan` and verify output paths

**Dependencies:** Task 1.1, Task 1.2

**Files likely touched:**
- `commands/plan.txt`

**Estimated scope:** S (1 file)

---

### Task 3.3: Update `/build` Command

**Description:** Update `commands/build.txt` to read the active spec and todo from `workflow_artifacts.json` state instead of assuming `tasks/todo.md`.

**Acceptance criteria:**
- [ ] Command template instructs agent to read `workflow_artifacts.read_workflow_artifacts()` to find the active spec and todo
- [ ] Falls back to `tasks/todo.md` if no state exists
- [ ] Falls back to legacy `SPEC.md` if no feature-scoped spec found
- [ ] Emits `phase_change` event when entering BUILD phase

**Verification:**
- [ ] Read updated command file
- [ ] Verify state-reading instructions are present

**Dependencies:** Task 1.1, Task 1.2

**Files likely touched:**
- `commands/build.txt`

**Estimated scope:** S (1 file)

---

### Task 3.4: Update `/review` Command

**Description:** Update `commands/review.txt` to read the active spec from state and write review reports to resolved paths.

**Acceptance criteria:**
- [ ] Command template instructs agent to read active spec from `workflow_artifacts.json`
- [ ] Review report path resolved via `workflow_artifacts.resolve_paths()` → `docs/reviews/<slug>.md`
- [ ] Falls back to legacy behavior if no state exists
- [ ] `markdown-documents` loaded as companion for report writing
- [ ] Emits `artifact_created` event on review creation

**Verification:**
- [ ] Read updated command file
- [ ] Verify state-reading and path-resolution instructions

**Dependencies:** Task 1.1, Task 1.2

**Files likely touched:**
- `commands/review.txt`

**Estimated scope:** S (1 file)

---

### Task 3.5: Update `/test` Command

**Description:** Update `commands/test.txt` to read the active spec from state for context.

**Acceptance criteria:**
- [ ] Command template instructs agent to read active spec from `workflow_artifacts.json`
- [ ] Falls back to legacy behavior if no state exists
- [ ] Emits `phase_change` event when entering VERIFY phase

**Verification:**
- [ ] Read updated command file

**Dependencies:** Task 1.1, Task 1.2

**Files likely touched:**
- `commands/test.txt`

**Estimated scope:** S (1 file)

---

### Task 3.6: Update `/ship` Command

**Description:** Update `commands/ship.py` to use the shared path resolver for spec discovery and report output, replacing its internal `_find_spec` with resolver-based lookup.

**Acceptance criteria:**
- [ ] `ship.py` imports and calls `workflow_artifacts.resolve_paths()` for spec and report paths
- [ ] `_find_spec` is updated to check `workflow_artifacts.json` first, then scan `docs/specs/`, then fall back to `SPEC.md`
- [ ] Ship report path resolved to `docs/reports/<slug>-ship.md`
- [ ] `workflow_artifacts.json` updated with `ship_report_path` after report creation
- [ ] All feature artifacts transitioned to `completed` lifecycle state
- [ ] Existing ship.py tests continue to pass

**Verification:**
- [ ] `pytest tests/test_ship_run.py tests/test_ship_sanitization.py -v`
- [ ] Manual check: ship command resolves spec from state

**Dependencies:** Task 1.1, Task 1.2, Task 1.3

**Files likely touched:**
- `commands/ship.py`
- `tests/test_ship_run.py` (possibly extend)

**Estimated scope:** M (2–3 files)

---

### Task 3.7: Update `/code-simplify` Command

**Description:** Update `commands/code-simplify.txt` to use resolved paths for any reports and read the active spec from state.

**Acceptance criteria:**
- [ ] Command template references `workflow_artifacts` for spec context when available
- [ ] Falls back gracefully when no state exists
- [ ] Emits `artifact_updated` events for simplified files

**Verification:**
- [ ] Read updated command file

**Dependencies:** Task 1.1, Task 1.2

**Files likely touched:**
- `commands/code-simplify.txt`

**Estimated scope:** XS (1 file)

---

### Checkpoint: Phase 3

- [ ] All 7 commands updated to use resolver
- [ ] No hardcoded legacy paths except in fallback logic
- [ ] `markdown-documents` companion loaded in document-producing commands
- [ ] Events emitted on artifact creation/updates
- [ ] Existing tests pass
- [ ] Manual walkthrough: `/spec` → `/plan` → `/build` with state flowing between them

---

## Phase 4: Approval + Lifecycle

### Task 4.1: Add `--approve` Flag Support to `/spec` and `/plan`

**Description:** Add approval instructions to the `/spec` and `/plan` command templates so that `--approve` marks the active artifact as approved.

**Acceptance criteria:**
- [ ] `/spec --approve` reads `workflow_artifacts.json`, sets `approved.spec = true`, saves, emits `approval` event
- [ ] `/plan --approve` reads `workflow_artifacts.json`, sets `approved.plan = true`, saves, emits `approval` event
- [ ] Approval is invalidated (set to `false`) when the artifact file is modified after approval
- [ ] The model cannot self-approve — only user-confirmed approval is accepted
- [ ] Approval state persists in `workflow_artifacts.json` and is rehydrated after compaction

**Verification:**
- [ ] Unit test: approval toggle works in `workflow_artifacts.json`
- [ ] Unit test: approval invalidation on file modification
- [ ] Read updated command files for `--approve` instructions

**Dependencies:** Task 1.2, Task 2.1, Task 3.1, Task 3.2

**Files likely touched:**
- `commands/spec.txt`
- `commands/plan.txt`
- `helpers/workflow_state.py` (add `mark_approved` helper)

**Estimated scope:** S (3 files)

---

### Task 4.2: Add Artifact Lifecycle States

**Description:** Implement lifecycle tracking for artifacts — `active`, `superseded`, `completed`.

**Acceptance criteria:**
- [ ] `lifecycle` field in `workflow_artifacts.json` maps artifact type to status (`active`, `superseded`, `completed`)
- [ ] Creating a new spec for the same slug supersedes the old one
- [ ] `/ship` completion transitions all feature artifacts to `completed`
- [ ] Lifecycle transitions emit `artifact_lifecycle` events
- [ ] Only `active` artifacts are included in handoff/rehydration

**Verification:**
- [ ] Unit test: new spec supersedes old spec
- [ ] Unit test: ship transitions all to completed
- [ ] Unit test: only active artifacts in handoff data
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 1.2, Task 2.1

**Files likely touched:**
- `helpers/workflow_state.py`

**Estimated scope:** S (1 file)

---

### Checkpoint: Phase 4

- [ ] Approval flow works: `/spec` → `/spec --approve` → state shows approved
- [ ] Lifecycle transitions work: create → supersede → complete
- [ ] Events emitted for approval and lifecycle changes
- [ ] All Phase 4 tests pass

---

## Phase 5: Rehydration + Handoff

### Task 5.1: Update Reattach Extension for No-Project Fallback

**Description:** Update `_67_reattach_workflow_state.py` (in `message_loop_prompts_after`) to check the no-project state fallback when no project is active.

**Acceptance criteria:**
- [ ] Extension calls `resolve_state_dir(agent)` which now handles no-project fallback
- [ ] When no project is active, rehydrates from `/a0/usr/workdir/.a0_agent_skills/state/`
- [ ] `workflow_artifacts.json` is included in rehydrated state block
- [ ] Active artifact paths (spec, plan, todo) appear in the rehydrated prompt
- [ ] Extension remains fail-safe (top-level try/except)
- [ ] Existing rehydration tests pass

**Verification:**
- [ ] `pytest tests/test_workflow_rehydrate.py -v` — all existing tests pass
- [ ] New test: no-project agent gets rehydrated state from workdir fallback
- [ ] New test: `workflow_artifacts.json` content appears in state block

**Dependencies:** Task 1.4, Task 1.2

**Files likely touched:**
- `extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py`
- `tests/test_workflow_rehydrate.py` (extend)

**Estimated scope:** S (2 files)

---

### Task 5.2: Update Handoff Format to Include Full Artifact Set

**Description:** Update `write_handoff()` in `workflow_state.py` to include active artifact paths, approval state, and follow the `agents-best-practices` compaction handoff format.

**Acceptance criteria:**
- [ ] `handoff.md` includes: Current objective, User constraints, Active plan and goal, Approval state, Resources inspected, Artifacts created/changed (with full paths), Tool calls and key results, Errors and fixes attempted, Open questions, Pending tasks, Next recommended step
- [ ] Active artifact paths read from `workflow_artifacts.json`
- [ ] Handoff generation remains fail-safe
- [ ] No-project mode generates handoff to fallback state dir

**Verification:**
- [ ] Unit test: handoff includes artifact paths section
- [ ] Unit test: handoff includes approval state
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 1.2, Task 1.4

**Files likely touched:**
- `helpers/workflow_state.py` (modify `write_handoff`)
- `tests/test_workflow_state.py` (extend)

**Estimated scope:** S (2 files)

---

### Task 5.3: Update Persist Extension to Save `workflow_artifacts.json`

**Description:** Ensure `_10_persist_workflow_state.py` triggers regeneration of `handoff.md` after `workflow_artifacts.json` changes.

**Acceptance criteria:**
- [ ] Persist extension recognizes when `workflow_artifacts.json` is written and triggers `write_handoff`
- [ ] Works in both project and no-project modes
- [ ] Extension remains fail-safe

**Verification:**
- [ ] `pytest tests/test_persist_workflow_state.py -v`
- [ ] Verify handoff regenerated after artifact state change

**Dependencies:** Task 1.2, Task 1.4

**Files likely touched:**
- `extensions/python/tool_execute_after/_10_persist_workflow_state.py`
- `tests/test_persist_workflow_state.py` (extend)

**Estimated scope:** S (2 files)

---

### Checkpoint: Phase 5

- [ ] Rehydration works in both project and no-project modes
- [ ] Handoff includes full artifact set with paths and approval state
- [ ] Persist extension triggers handoff regeneration
- [ ] All Phase 5 tests pass
- [ ] Simulate compaction: verify agent recovers with full context

---

## Phase 6: Testing

### Task 6.1: Unit Tests for Path Resolver

**Description:** Comprehensive unit tests for `helpers/workflow_state.py` covering all path resolution scenarios.

**Acceptance criteria:**
- [ ] Tests cover: project-mode resolution, no-project-mode resolution, slug from state, slug from filesystem, slug from override, multiple-spec disambiguation, no-spec case
- [ ] Tests cover: `state_root` reads config correctly
- [ ] Tests cover: corrupted/empty state files handled gracefully
- [ ] Tests cover: auto-creation of target directories
- [ ] All tests pass in isolation and as a suite

**Verification:**
- [ ] `pytest tests/test_workflow_state.py -v` — all tests pass
- [ ] Coverage report shows >90% for `workflow_state.py`

**Dependencies:** Task 1.1

**Files likely touched:**
- `tests/test_workflow_state.py` (new or extended)

**Estimated scope:** S (1 file)

---

### Task 6.2: Unit Tests for Typed Events

**Description:** Unit tests verifying typed event emission format and correctness.

**Acceptance criteria:**
- [ ] Tests cover all 5 event types: `artifact_created`, `artifact_updated`, `phase_change`, `approval`, `artifact_lifecycle`
- [ ] Tests verify ISO 8601 timestamps
- [ ] Tests verify slug and path included in relevant events
- [ ] Tests verify events appended without corrupting existing log
- [ ] Tests verify backward compatibility with untyped events

**Verification:**
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 2.1, Task 2.2

**Files likely touched:**
- `tests/test_workflow_state.py`

**Estimated scope:** S (1 file)

---

### Task 6.3: Unit Tests for Approval and Lifecycle

**Description:** Unit tests for approval marking, invalidation, and lifecycle transitions.

**Acceptance criteria:**
- [ ] Tests: mark spec approved → `approved.spec == true`
- [ ] Tests: modify artifact after approval → approval invalidated
- [ ] Tests: new spec supersedes old → old lifecycle = `superseded`
- [ ] Tests: ship completes → all artifacts lifecycle = `completed`
- [ ] Tests: only active artifacts in handoff data

**Verification:**
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** Task 4.1, Task 4.2

**Files likely touched:**
- `tests/test_workflow_state.py`

**Estimated scope:** S (1 file)

---

### Task 6.4: Integration Tests for Commands

**Description:** End-to-end tests proving that commands use resolved paths correctly.

**Acceptance criteria:**
- [ ] Test: `/spec` writes to `docs/specs/<slug>-spec.md` and updates `workflow_artifacts.json`
- [ ] Test: `/plan` writes to `docs/plans/<slug>-plan.md` and updates `workflow_artifacts.json`
- [ ] Test: `/build` reads active todo from state
- [ ] Test: `/review` reads active spec from state and writes to resolved review path
- [ ] Test: Legacy fallback works when `SPEC.md` exists but no feature-scoped spec

**Verification:**
- [ ] `pytest tests/test_command_integration.py -v`

**Dependencies:** Phase 3 complete

**Files likely touched:**
- `tests/test_command_integration.py` (existing, extended)

**Estimated scope:** M (1 new test file)

---

### Task 6.5: Integration Test for Rehydration

**Description:** End-to-end test proving that rehydration after simulated compaction recovers full artifact context.

**Acceptance criteria:**
- [ ] Test: create artifacts, write state, simulate compaction (clear agent data), rehydrate → agent sees full artifact set
- [ ] Test works in both project and no-project modes
- [ ] Test: `workflow_artifacts.json` content appears in rehydrated prompt block
- [ ] Test: handoff.md includes artifact paths

**Verification:**
- [ ] `pytest tests/test_workflow_rehydrate.py -v`

**Dependencies:** Phase 5 complete

**Files likely touched:**
- `tests/test_workflow_rehydrate.py` (extend)

**Estimated scope:** M (1 file)

---

### Task 6.6: Regression Tests

**Description:** Tests protecting against specific failure modes identified in the spec.

**Acceptance criteria:**
- [ ] Test: no `workdir/.a0proj` directory is ever created
- [ ] Test: commands never fall back to `SPEC.md` hardcoding when feature-scoped paths are available
- [ ] Test: no-project mode does not lose plugin-local state
- [ ] Test: existing `test_workflow_state.py` tests still pass unmodified

**Verification:**
- [ ] `pytest tests/ -v` — full suite green

**Dependencies:** All previous phases

**Files likely touched:**
- `tests/test_workflow_state.py` (extend)

**Estimated scope:** S (1 file)

---

### Checkpoint: Phase 6

- [ ] Full test suite passes: `pytest tests/ -v`
- [ ] No existing tests broken
- [ ] Coverage >90% for `helpers/workflow_state.py`
- [ ] Integration tests prove end-to-end flow
- [ ] Regression tests protect against known failure modes
- [ ] Ready for human review and merge

---

## Summary

| Phase | Tasks | Est. Files | Dependencies |
|-------|-------|-----------|-------------|
| 1. Foundation | 1.1–1.4 | 3–4 new/modified | None |
| 2. Event Model | 2.1–2.2 | 1 modified | Phase 1 |
| 3. Command Alignment | 3.1–3.7 | 7–8 modified | Phase 1 |
| 4. Approval + Lifecycle | 4.1–4.2 | 3 modified | Phase 1 + 2 |
| 5. Rehydration + Handoff | 5.1–5.3 | 4–5 modified | Phase 1 + 4 |
| 6. Testing | 6.1–6.6 | 3–4 new/extended | All phases |
| **Total** | **22 tasks** | **~21 files** | — |

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Command templates too vague for agent to follow correctly | High — agent ignores resolver | Medium | Include explicit code snippets and function call examples in command templates |
| No-project state directory conflicts with user files | Medium | Low | Use `.a0_agent_skills/` hidden directory; document the convention |
| Legacy fallback creates ambiguous behavior | Medium | Medium | Strict precedence: feature-scoped → legacy → prompt user |
| `workflow_artifacts.json` grows stale after manual file changes | Medium | High | Check file existence on read; emit warning if referenced file missing |
| Breaking existing tests during Phase 1.4 | High | Low | Run full suite after `resolve_state_dir` changes; extend don't modify |
| Agent context too large with full artifact paths in rehydration | Low | Medium | Summarize artifact paths; only include active (not superseded) |
| Ship.py refactor breaks spec-reading logic | High | Low | Keep `_find_spec` as fallback; add new resolver-based path alongside |

## Open Questions

1. Should `promptinclude` be extended with additional patterns for active specs/plans in a future iteration? (Spec: deferred)
2. Should spec summaries be auto-saved to `.a0proj/knowledge/` for semantic recall? (Spec: deferred)
3. Should `validate-skills.js` be ported to Python for Agent Zero CI? (Spec: deferred)
4. Should the persist extension auto-detect `workflow_artifacts.json` changes, or should commands call `write_handoff` explicitly? (Implementation decision)
5. Should `/build` auto-advance the phase in `workflow_artifacts.json`, or only emit an event? (Implementation decision)
