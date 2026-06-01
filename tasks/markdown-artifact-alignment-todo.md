# Todo: Markdown Artifact and State Alignment

> Simplified from 22 tasks to 10, based on implementation audit.
> Audit found 12 items already done, 4 overengineered items deferred.
> Real scope: ~200 lines new Python + 4 text file edits.

## Phase 1: Core Path Resolver

- [x] **Task 1:** Add `resolve_visible_root(agent)` to `helpers/workflow_state.py`
  - Returns project root if project selected, `/a0/usr/workdir` if not
  - ~10 lines
  - Acceptance: returns correct root in both modes
  - Verify: `pytest tests/test_workflow_state.py -v` ✅ 3 tests pass
  - Files: `helpers/workflow_state.py`, `tests/test_workflow_state.py`
  - Scope: S

- [x] **Task 2:** Add `resolve_artifact_paths(agent, slug=None)` to `helpers/workflow_state.py`
  - Returns dict with all canonical artifact paths (spec, plan, todo, idea, adr, report)
  - Uses `resolve_visible_root()` + `resolve_state_dir()` under the hood
  - Falls back to legacy paths (`SPEC.md`, `tasks/plan.md`, `tasks/todo.md`) when no slug
  - ~30 lines
  - Acceptance: returns correct paths for project and no-project modes
  - Verify: `pytest tests/test_workflow_state.py -v` ✅ 5 tests pass
  - Files: `helpers/workflow_state.py`, `tests/test_workflow_state.py`
  - Scope: S

- [x] **Task 3:** Add `discover_feature_slug(agent)` and `save/read_workflow_artifacts()` to `helpers/workflow_state.py`
  - Slug from state or filesystem scan of `docs/specs/*-spec.md`
  - Read/write `workflow_artifacts.json` using existing `_save_artifact`/`_read_artifact`
  - ~40 lines
  - Acceptance: slug discovered from existing spec or stored in state
  - Verify: `pytest tests/test_workflow_state.py -v` ✅ 7 tests pass
  - Files: `helpers/workflow_state.py`, `tests/test_workflow_state.py`
  - Scope: S

- [x] **Task 4:** Fix `resolve_state_dir()` — add no-project fallback + read config
  - When no project: return `/a0/usr/workdir/.a0_agent_skills/state/`
  - Read `default_config.yaml.workflow_state_path` instead of hardcoding
  - ~15 lines changed
  - Acceptance: state dir resolves in no-project mode; config key is respected
  - Verify: `pytest tests/test_workflow_state.py -v` ✅ 5 tests updated, pass
  - Files: `helpers/workflow_state.py`, `tests/test_workflow_state.py`
  - Scope: S

### Checkpoint 1: Path Resolver Complete
- [x] All 4 tasks pass tests
- [x] `resolve_artifact_paths()` works in both project and no-project modes
- [x] Legacy fallback works when no slug is set
- [x] 510+ existing tests still pass

---

## Phase 2: Command Alignment

- [x] **Task 5:** Update `commands/spec.txt` — use resolver + load `markdown-documents`
  - Replace hardcoded `SPEC.md` with resolver path ✅
  - Add `markdown-documents` as companion skill ✅
  - Files: `commands/spec.txt`
  - Scope: XS

- [x] **Task 6:** Update `commands/plan.txt` — use resolver + load `markdown-documents`
  - Replace hardcoded `tasks/plan.md` / `tasks/todo.md` with resolver paths ✅
  - Add `markdown-documents` as companion skill ✅
  - Files: `commands/plan.txt`
  - Scope: XS

- [x] **Task 7:** Update `commands/build.txt` — read active spec/todo from state
  - Replace hardcoded `tasks/todo.md` with resolver path ✅
  - Read active spec for success criteria when available ✅
  - Files: `commands/build.txt`
  - Scope: XS

- [x] **Task 8:** Update `commands/review.txt`, `commands/test.txt`, `commands/code-simplify.txt`
  - Read active spec from state for review boundaries and test criteria ✅
  - Replace any hardcoded `SPEC.md` references ✅
  - Files: `commands/review.txt`, `commands/test.txt`, `commands/code-simplify.txt`
  - Scope: XS

### Checkpoint 2: Commands Aligned
- [x] No command hardcodes `SPEC.md`, `tasks/plan.md`, or `tasks/todo.md`
- [x] All commands resolve paths through `workflow_state.py`
- [x] `/spec` and `/plan` load `markdown-documents` companion

---

## Phase 3: Enhancement

- [x] **Task 9:** Update reattach + handoff extensions
  - Reattach: add no-project fallback (read `workdir/.a0_agent_skills/state/`) ✅
  - Handoff: include artifact paths in `handoff.md` ✅
  - Persist: emit typed artifact events (`artifact_created`, `artifact_updated`) ✅
  - Files: extensions in `message_loop_prompts_after/`, `tool_execute_after/`
  - Scope: M

- [x] **Task 10:** Add `--approve` mechanism
  - Add `--approve` flag handling in `/spec` and `/plan` commands ✅
  - Record approval in `workflow_artifacts.json` ✅
  - Emit `approval` typed event ✅
  - Files: `commands/spec.txt`, `commands/plan.txt`, `helpers/workflow_state.py`
  - Scope: S

### Checkpoint 3: Complete
- [x] No-project rehydration works
- [x] Handoff includes artifact paths
- [x] Typed events emit for artifact and approval actions
- [x] `--approve` records approval state
- [x] All tests pass (642+ existing + new)

---

## Deferred (not in scope)

- Artifact lifecycle states (active/superseded/completed) — no consumer yet
- Approval invalidation on material changes — premature
- `--slug` override — auto-discovery is sufficient
- Multi-spec disambiguation — only one active spec at a time
- `helpers/spec_reader.py` extraction — stays in ship.py
- validate-skills.js port to Python — separate concern

---

## SHIPPED — 2026-05-30

**Feature:** Markdown Artifact Path Resolution & Alignment
**Date shipped:** 2026-05-30
**Status:** ✅ COMPLETE — all 10 tasks done, code review APPROVED

### Summary
Canonical artifact path resolution system for the a0_agent_skills plugin.
Single source of truth for spec, plan, todo, idea, adr, and report paths.
Works in both project and no-project modes with legacy fallback.

### Key Deliverables
- 5 new functions in `helpers/workflow_state.py`: resolve_visible_root, resolve_artifact_paths, discover_feature_slug, save_workflow_artifacts, read_workflow_artifacts
- 6 command templates migrated to resolver (spec, plan, build, review, test, code-simplify)
- Typed artifact events (artifact_created, artifact_updated, approval)
- `--approve` mechanism in spec and plan commands
- No-project rehydration fallback in reattach extension
- 89 workflow_state tests (all pass), 650 total tests pass
- Code review APPROVED, 12 findings fixed, code simplified

### Files Changed
- 27 files, 937 insertions(+), 110 deletions(-)
- ADR: docs/adrs/007-artifact-path-resolution.md
